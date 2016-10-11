import datetime
import json
import re
import uuid
import cachemodel
from allauth.account.adapter import get_adapter

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import ProtectedError
from django.template.loader import get_template

from openbadges_bakery import bake

from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.models import (AbstractIssuer, AbstractBadgeClass,
                             AbstractBadgeInstance, EmailBlacklist)
from mainsite.utils import OriginSetting
from pathway.tasks import award_badges_for_pathway_completion

from .utils import generate_sha256_hashstring, badgr_import_url, CURRENT_OBI_CONTEXT_IRI


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Issuer(AbstractIssuer):
    owner = models.ForeignKey(AUTH_USER_MODEL, related_name='issuers',
                              on_delete=models.PROTECT, null=False)
    staff = models.ManyToManyField(AUTH_USER_MODEL, through='IssuerStaff')
    cached = SlugOrJsonIdCacheModelManager()

    def publish(self, *args, **kwargs):
        super(Issuer, self).publish(*args, **kwargs)
        self.owner.publish()
        for member in self.cached_staff():
            member.publish()

    def delete(self, *args, **kwargs):
        if len(self.cached_badgeclasses()) > 0:
            raise ProtectedError("Issuer may only be deleted after all its defined BadgeClasses have been deleted.")

        staff = self.cached_staff()
        owner = self.owner
        super(Issuer, self).delete(*args, **kwargs)
        owner.publish()
        for member in staff:
            member.publish()

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return self.staff.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_editors(self):
        UserModel = get_user_model()
        return UserModel.objects.filter(issuerstaff__issuer=self, issuerstaff__editor=True)

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        return self.badgeclasses.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathways(self):
        return self.pathway_set.filter(is_active=True)

    @cachemodel.cached_method(auto_publish=True)
    def cached_recipient_groups(self):
        return self.recipientgroup_set.all()

    @property
    def image_preview(self):
        return self.image


class IssuerStaff(models.Model):
    issuer = models.ForeignKey(Issuer)
    user = models.ForeignKey(AUTH_USER_MODEL)
    editor = models.BooleanField(default=False)

    class Meta:
        unique_together = ('issuer', 'user')


class BadgeClass(AbstractBadgeClass):
    issuer = models.ForeignKey(Issuer, blank=False, null=False,
                               on_delete=models.CASCADE,
                               related_name="badgeclasses")
    cached = SlugOrJsonIdCacheModelManager()

    def publish(self):
        super(BadgeClass, self).publish()
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        if self.recipient_count() > 0:
            raise ProtectedError("BadgeClass may only be deleted if all BadgeInstances have been revoked.")

        issuer = self.issuer
        super(BadgeClass, self).delete(*args, **kwargs)
        issuer.publish()

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @cachemodel.cached_method(auto_publish=True)
    def recipient_count(self):
        return self.badgeinstances.filter(revoked=False).count()

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return self.badgeinstances.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathway_elements(self):
        return [peb.element for peb in self.pathwayelementbadge_set.all()]

    def issue(self, recipient_id=None, evidence_url=None, notify=False, created_by=None):
        return BadgeInstance.objects.create_badgeinstance(
            badgeclass=self, recipient_id=recipient_id, evidence_url=evidence_url,
            notify=notify, created_by=created_by
        )


class BadgeInstanceManager(models.Manager):
    def create_badgeinstance(
            self, badgeclass, recipient_id, evidence_url=None,
            notify=False, check_completions=True, created_by=None
    ):
        """
        Convenience method to award a badge to a recipient_id
        :type badgeclass: BadgeClass
        :type recipient_id: str
        :type issuer: Issuer
        :type evidence_url: str
        :type notify: bool
        :type check_completions: bool
        """
        new_instance = BadgeInstance(
            badgeclass=badgeclass, issuer=badgeclass.issuer, recipient_identifier=recipient_id,
        )

        new_instance.json = {
            # 'id': TO BE ADDED IN SAVE
            '@context': CURRENT_OBI_CONTEXT_IRI,
            'type': 'Assertion',
            'recipient': {
                'type': 'email',
                'hashed': True
                # 'identity': TO BE ADDED IN SAVE
            },
            'badge': badgeclass.get_full_url(),
            'verify': {
                'type': 'hosted'
                # 'url': TO BE ADDED IN SAVE
            }
        }

        if evidence_url:
            new_instance.json['evidence'] = evidence_url

        new_instance.slug = new_instance.get_new_slug()

        # Augment json with id
        full_url = new_instance.get_full_url()
        new_instance.json['id'] = full_url
        new_instance.json['uid'] = new_instance.slug
        new_instance.json['verify']['url'] = full_url
        new_instance.json['image'] = full_url + '/image'

        new_instance.save()

        if check_completions:
            award_badges_for_pathway_completion.delay(new_instance.slug)

        if notify:
            new_instance.notify_earner()

        return new_instance


class BadgeInstance(AbstractBadgeInstance):
    badgeclass = models.ForeignKey(BadgeClass, blank=False, null=False,
                                   on_delete=models.CASCADE,
                                   related_name='badgeinstances')
    issuer = models.ForeignKey(Issuer, blank=False, null=False)

    ACCEPTANCE_UNACCEPTED = 'Unaccepted'
    ACCEPTANCE_ACCEPTED = 'Accepted'
    ACCEPTANCE_REJECTED = 'Rejected'
    ACCEPTANCE_CHOICES = (
        (ACCEPTANCE_UNACCEPTED, 'Unaccepted'),
        (ACCEPTANCE_ACCEPTED, 'Accepted'),
        (ACCEPTANCE_REJECTED, 'Rejected'),
    )
    acceptance = models.CharField(max_length=254, choices=ACCEPTANCE_CHOICES, default=ACCEPTANCE_ACCEPTED)

    objects = BadgeInstanceManager()

    @property
    def extended_json(self):
        extended_json = self.json
        extended_json['badge'] = self.badgeclass.json
        extended_json['badge']['issuer'] = self.issuer.json

        return extended_json

    def image_url(self):
        if getattr(settings, 'MEDIA_URL').startswith('http'):
            return default_storage.url(self.image.name)
        else:
            return getattr(settings, 'HTTP_ORIGIN') + default_storage.url(self.image.name)

    @property
    def share_url(self):
        return OriginSetting.HTTP+reverse('shared_badge', kwargs={'badge_id': self.slug})

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @property
    def cached_badgeclass(self):
        # memoized to improve performance
        if not hasattr(self, '_cached_badgeclass'):
            self._cached_badgeclass = BadgeClass.cached.get(pk=self.badgeclass_id)
        return self._cached_badgeclass

    def get_absolute_url(self):
        return reverse('badgeinstance_json', kwargs={'slug': self.slug})

    @staticmethod
    def get_new_slug():
        return str(uuid.uuid4())

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.json['recipient']['salt'] = salt = self.get_new_slug()
            self.json['recipient']['identity'] = \
                generate_sha256_hashstring(self.recipient_identifier, salt)

            self.created_at = datetime.datetime.now()
            self.json['issuedOn'] = self.created_at.isoformat()

            imageFile = default_storage.open(self.badgeclass.image.file.name)
            self.image = bake(imageFile, json.dumps(self.json, indent=2))

            self.image.open()

        if self.revoked is False:
            self.revocation_reason = None

        super(BadgeInstance, self).save(*args, **kwargs)

    def publish(self):
        super(BadgeInstance, self).publish()
        self.badgeclass.publish()
        if self.cached_recipient_profile:
            self.cached_recipient_profile.publish()
        self.publish_by('slug')

    def delete(self, *args, **kwargs):
        badgeclass = self.badgeclass
        recipient_profile = self.cached_recipient_profile
        super(BadgeInstance, self).delete(*args, **kwargs)
        badgeclass.publish()
        if recipient_profile:
            recipient_profile.publish()
        self.publish_delete('slug')

    def notify_earner(self):
        """
        Sends an email notification to the badge earner.
        This process involves creating a badgeanalysis.models.OpenBadge
        returns the EarnerNotification instance.

        TODO: consider making this an option on initial save and having a foreign key to
        the notification model instance (which would link through to the OpenBadge)
        """
        try:
            EmailBlacklist.objects.get(email=self.recipient_identifier)
        except EmailBlacklist.DoesNotExist:
            # Allow sending, as this email is not blacklisted.
            pass
        else:
            return
            # TODO: Report email non-delivery somewhere.

        try:
            if self.issuer.image:
                issuer_image_url = self.issuer.get_full_url() + '/image'
            else:
                issuer_image_url = None

            email_context = {
                'badge_name': self.badgeclass.name,
                'badge_description': self.badgeclass.prop('description'),
                'issuer_name': re.sub(r'[^\w\s]+', '', self.issuer.name, 0, re.I),
                'issuer_url': self.issuer.prop('url'),
                'issuer_image_url': issuer_image_url,
                'badge_instance_url': self.get_full_url(),
                'image_url': self.get_full_url() + '/image',
                'badgr_import_url': badgr_import_url(self),
                'unsubscribe_url': getattr(settings, 'HTTP_ORIGIN') + EmailBlacklist.generate_email_signature(self.recipient_identifier)
            }
        except KeyError as e:
            # A property isn't stored right in json
            raise e

        adapter = get_adapter()
        adapter.send_mail('issuer/email/notify_earner', self.recipient_identifier, context=email_context)

    @property
    def cached_recipient_profile(self):
        from recipient.models import RecipientProfile
        try:
            return RecipientProfile.cached.get(recipient_identifier=self.recipient_identifier)
        except RecipientProfile.DoesNotExist:
            return None

    @property
    def recipient_user(self):
        from badgeuser.models import CachedEmailAddress
        try:
            email_address = CachedEmailAddress.cached.get(email=self.recipient_identifier)
            if email_address.verified:
                return email_address.user
        except CachedEmailAddress.DoesNotExist:
            pass
        return None
