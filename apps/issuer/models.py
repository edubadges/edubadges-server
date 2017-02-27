from __future__ import unicode_literals

import datetime
import json
import re
import uuid

import cachemodel
from allauth.account.adapter import get_adapter
from autoslug import AutoSlugField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import ProtectedError
from django.utils.timezone import get_current_timezone
from jsonfield import JSONField
from openbadges_bakery import bake

from issuer.managers import BadgeInstanceManager
from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.mixins import ResizeUploadedImage
from mainsite.models import (AbstractIssuer, AbstractBadgeClass,
                             AbstractBadgeInstance, BadgrApp, EmailBlacklist)
from mainsite.utils import OriginSetting
from .utils import generate_sha256_hashstring, CURRENT_OBI_CONTEXT_IRI

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Issuer(ResizeUploadedImage, cachemodel.CacheModel):
    source = models.CharField(max_length=254, default='local')
    source_url = models.CharField(max_length=254, blank=True, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, related_name="+")

    staff = models.ManyToManyField(AUTH_USER_MODEL, through='IssuerStaff')

    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)
    name = models.CharField(max_length=1024)
    image = models.FileField(upload_to='uploads/issuers', blank=True, null=True)
    description = models.TextField(blank=True, null=True, default=None)
    url = models.CharField(max_length=254, blank=True, null=True, default=None)
    email = models.CharField(max_length=254, blank=True, null=True, default=None)

    old_json = JSONField()
    original_json = models.TextField(blank=True, null=True, default=None)

    cached = SlugOrJsonIdCacheModelManager()

    def publish(self, *args, **kwargs):
        super(Issuer, self).publish(*args, **kwargs)
        self.publish_by('slug')
        for member in self.cached_staff():
            member.publish()

    def delete(self, *args, **kwargs):
        if len(self.cached_badgeclasses()) > 0:
            raise ProtectedError("Issuer may only be deleted after all its defined BadgeClasses have been deleted.")

        staff = self.cached_staff()
        super(Issuer, self).delete(*args, **kwargs)
        self.publish_delete("slug")
        for member in staff:
            member.publish()

    def get_absolute_url(self):
        return reverse('issuer_json', kwargs={'slug': self.slug})

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def jsonld_id(self):
        return OriginSetting.JSON + self.get_absolute_url()

    @property
    def editors(self):
        return self.staff.filter(issuerstaff__role__in=(IssuerStaff.ROLE_EDITOR, IssuerStaff.ROLE_OWNER))

    @property
    def owners(self):
        return self.staff.filter(issuerstaff__role=IssuerStaff.ROLE_OWNER)

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return self.staff.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_editors(self):
        UserModel = get_user_model()
        return UserModel.objects.filter(issuerstaff__issuer=self, issuerstaff__role=IssuerStaff.ROLE_EDITOR)

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

    def get_json(self):
        json = {
            '@context': CURRENT_OBI_CONTEXT_IRI,
            'type': 'Issuer',
            'id': self.jsonld_id,
            'name': self.name,
            'url': self.url,
            'email': self.email,
            'description': self.description,
        }
        if self.image:
            json['image'] = OriginSetting.HTTP + reverse('issuer_image', kwargs={'slug': self.slug})
        return json

    @property
    def json(self):
        return self.get_json()


class IssuerStaff(models.Model):
    ROLE_OWNER = 'owner'
    ROLE_EDITOR = 'editor'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = (
        (ROLE_OWNER, 'Owner'),
        (ROLE_EDITOR, 'Editor'),
        (ROLE_STAFF, 'Staff'),
    )
    issuer = models.ForeignKey(Issuer)
    user = models.ForeignKey(AUTH_USER_MODEL)
    role = models.CharField(max_length=254, choices=ROLE_CHOICES, default=ROLE_STAFF)

    class Meta:
        unique_together = ('issuer', 'user')


class BadgeClass(ResizeUploadedImage, cachemodel.CacheModel):
    source = models.CharField(max_length=254, default='local')
    source_url = models.CharField(max_length=254, blank=True, null=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, related_name="+")
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.CASCADE, related_name="badgeclasses")

    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='uploads/badges', blank=True)
    description = models.TextField(blank=True, null=True, default=None)

    criteria_url = models.CharField(max_length=254, blank=True, null=True, default=None)
    criteria_text = models.TextField(blank=True, null=True)

    old_json = JSONField()
    original_json = models.TextField(blank=True, null=True, default=None)

    cached = SlugOrJsonIdCacheModelManager()

    class Meta:
        verbose_name_plural = "Badge classes"

    def publish(self):
        super(BadgeClass, self).publish()
        self.issuer.publish()
        self.publish_by('slug')

    def delete(self, *args, **kwargs):
        if self.recipient_count() > 0:
            raise ProtectedError("BadgeClass may only be deleted if all BadgeInstances have been revoked.")

        if self.pathway_element_count() > 0:
            raise ProtectedError("BadgeClass may only be deleted if all PathwayElementBadge have been removed.")

        issuer = self.issuer
        super(BadgeClass, self).delete(*args, **kwargs)
        self.publish_delete('slug')
        issuer.publish()

    def get_absolute_url(self):
        return reverse('badgeclass_json', kwargs={'slug': self.slug})

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def jsonld_id(self):
        return OriginSetting.JSON + self.get_absolute_url()

    def get_criteria_url(self):
        if self.criteria_url:
            return self.criteria_url
        return OriginSetting.HTTP+reverse('badgeclass_criteria', kwargs={'slug': self.slug})

    @property
    def owners(self):
        return self.issuer.owners

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @cachemodel.cached_method(auto_publish=True)
    def recipient_count(self):
        return self.badgeinstances.filter(revoked=False).count()

    def pathway_element_count(self):
        return len(self.cached_pathway_elements())

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return self.badgeinstances.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathway_elements(self):
        return [peb.element for peb in self.pathwayelementbadge_set.all()]

    @cachemodel.cached_method(auto_publish=True)
    def cached_completion_elements(self):
        return [pce for pce in self.completion_elements.all()]

    def issue(self, recipient_id=None, evidence_url=None, notify=False, created_by=None, allow_uppercase=False, badgr_app=None):
        return BadgeInstance.objects.create_badgeinstance(
            badgeclass=self, recipient_id=recipient_id, evidence_url=evidence_url,
            notify=notify, created_by=created_by, allow_uppercase=allow_uppercase,
            badgr_app=badgr_app
        )

    def get_json(self):
        json = {
            '@context': CURRENT_OBI_CONTEXT_IRI,
            'type': 'BadgeClass',
            'id': self.jsonld_id,
            'name': self.name,
            'description': self.description,
            'issuer': self.cached_issuer.jsonld_id,
            "criteria": self.get_criteria_url(),
        }
        if self.image:
            json['image'] = OriginSetting.HTTP + reverse('badgeclass_image', kwargs={'slug': self.slug})
        return json

    @property
    def json(self):
        return self.get_json()


class BadgeInstance(ResizeUploadedImage, cachemodel.CacheModel):
    badgeclass = models.ForeignKey(BadgeClass, blank=False, null=False, on_delete=models.CASCADE, related_name='badgeinstances')
    issuer = models.ForeignKey(Issuer, blank=False, null=False)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, related_name="+")

    recipient_identifier = models.EmailField(max_length=1024, blank=False, null=False)
    image = models.FileField(upload_to='uploads/badges', blank=True)
    slug = AutoSlugField(max_length=255, populate_from='get_new_slug', unique=True, blank=False, editable=False)

    revoked = models.BooleanField(default=False)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)

    ACCEPTANCE_UNACCEPTED = 'Unaccepted'
    ACCEPTANCE_ACCEPTED = 'Accepted'
    ACCEPTANCE_REJECTED = 'Rejected'
    ACCEPTANCE_CHOICES = (
        (ACCEPTANCE_UNACCEPTED, 'Unaccepted'),
        (ACCEPTANCE_ACCEPTED, 'Accepted'),
        (ACCEPTANCE_REJECTED, 'Rejected'),
    )
    acceptance = models.CharField(max_length=254, choices=ACCEPTANCE_CHOICES, default=ACCEPTANCE_UNACCEPTED)

    salt = models.CharField(max_length=254, blank=True, null=True, default=None)
    evidence_url = models.CharField(max_length=254, blank=True, null=True, default=None)

    old_json = JSONField()

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

    @property
    def jsonld_id(self):
        return OriginSetting.JSON + self.get_absolute_url()

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def owners(self):
        return self.issuer.owners

    @staticmethod
    def get_new_slug():
        return str(uuid.uuid4())

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.salt = salt = self.get_new_slug()
            self.created_at = datetime.datetime.now()

            imageFile = default_storage.open(self.badgeclass.image.file.name)
            self.image = bake(imageFile, json.dumps(self.json, indent=2))

            self.image.open()

            try:
                from badgeuser.models import CachedEmailAddress
                existing_email = CachedEmailAddress.cached.get(email=self.recipient_identifier)
                if self.recipient_identifier != existing_email.email and \
                        self.recipient_identifier not in [e.email for e in existing_email.cached_variants()]:
                    existing_email.add_variant(self.recipient_identifier)
            except CachedEmailAddress.DoesNotExist:
                pass

        if self.revoked is False:
            self.revocation_reason = None

        super(BadgeInstance, self).save(*args, **kwargs)

    def publish(self):
        super(BadgeInstance, self).publish()
        self.badgeclass.publish()
        if self.cached_recipient_profile:
            self.cached_recipient_profile.publish()
        self.publish_by('slug')
        self.publish_by('slug', 'revoked')

    def delete(self, *args, **kwargs):
        badgeclass = self.badgeclass
        recipient_profile = self.cached_recipient_profile
        super(BadgeInstance, self).delete(*args, **kwargs)
        badgeclass.publish()
        if recipient_profile:
            recipient_profile.publish()
        self.publish_delete('slug')
        self.publish_delete('slug', 'revoked')

    def notify_earner(self, badgr_app=None):
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

        if badgr_app is None:
            badgr_app = BadgrApp.objects.get_current(None)

        try:
            if self.issuer.image:
                issuer_image_url = self.issuer.public_url + '/image'
            else:
                issuer_image_url = None

            email_context = {
                'badge_name': self.badgeclass.name,
                'badge_id': self.slug,
                'badge_description': self.badgeclass.description,
                'issuer_name': re.sub(r'[^\w\s]+', '', self.issuer.name, 0, re.I),
                'issuer_url': self.issuer.url,
                'issuer_detail': self.issuer.public_url,
                'issuer_image_url': issuer_image_url,
                'badge_instance_url': self.public_url,
                'image_url': self.public_url + '/image',
                'download_url': self.public_url + "?action=download",
                'unsubscribe_url': getattr(settings, 'HTTP_ORIGIN') + EmailBlacklist.generate_email_signature(
                    self.recipient_identifier),
                'site_name': badgr_app.name,
                'site_url': badgr_app.signup_redirect,
            }
            if badgr_app.cors == 'badgr.io':
                email_context['promote_mobile'] = True
        except KeyError as e:
            # A property isn't stored right in json
            raise e

        template_name = 'issuer/email/notify_earner'
        try:
            from badgeuser.models import CachedEmailAddress
            CachedEmailAddress.objects.get(email=self.recipient_identifier, verified=True)
            template_name = 'issuer/email/notify_account_holder'
            email_context['site_url'] = badgr_app.email_confirmation_redirect
        except CachedEmailAddress.DoesNotExist:
            pass

        adapter = get_adapter()
        adapter.send_mail(template_name, self.recipient_identifier, context=email_context)

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

    def get_json(self):
        json = {
            '@context': CURRENT_OBI_CONTEXT_IRI,
            'type': 'Assertion',
            'id': self.jsonld_id,
            # "issuedOn": self.created_at.astimezone(get_current_timezone()).replace(tzinfo=None).isoformat(),
            "uid": self.slug,
            "image": OriginSetting.HTTP + reverse('badgeinstance_image', kwargs={'slug': self.slug}),
            "badge": self.cached_badgeclass.jsonld_id,
            "verify": {
                "url": self.public_url,
                "type": "hosted"
            }
        }

        if self.evidence_url:
            json['evidence'] = self.evidence_url

        # FIXME: this is a hack to deal with naive datetimes with microseconds that were serialized...
        try:
            self._meta.get_field_by_name('old_json')
            if self.old_json and 'issuedOn' in self.old_json:
                json['issuedOn'] = self.old_json['issuedOn']
        except KeyError:
            pass

        if self.salt:
            json['recipient'] = {
                "type": "email",
                "salt": self.salt,
                "hashed": True,
                "identity": generate_sha256_hashstring(self.recipient_identifier.lower(), self.salt),
            }
        else:
            json['recipient'] = {
                "type": "email",
                "hashed": False,
                "identity": self.recipient_identifier
            }
        return json

    @property
    def json(self):
        return self.get_json()
