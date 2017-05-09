from __future__ import unicode_literals

import datetime
import json
import re
import uuid
from itertools import chain

import cachemodel
from allauth.account.adapter import get_adapter
from django.apps import apps
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.core.urlresolvers import reverse
from django.db import models, transaction
from django.db.models import ProtectedError
from jsonfield import JSONField
from openbadges_bakery import bake

from issuer.managers import BadgeInstanceManager
from entity.models import BaseVersionedEntity
from mainsite.managers import SlugOrJsonIdCacheModelManager
from mainsite.mixins import ResizeUploadedImage, ScrubUploadedSvgImage
from mainsite.models import (BadgrApp, EmailBlacklist)
from mainsite.utils import OriginSetting
from .utils import generate_sha256_hashstring, CURRENT_OBI_CONTEXT_IRI

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class BaseAuditedModel(cachemodel.CacheModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('badgeuser.BadgeUser', blank=True, null=True, related_name="+")

    class Meta:
        abstract = True

    @property
    def cached_creator(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(id=self.created_by_id)


class Issuer(ResizeUploadedImage, ScrubUploadedSvgImage, BaseAuditedModel, BaseVersionedEntity):
    entity_class_name = 'Issuer'

    source = models.CharField(max_length=254, default='local')
    source_url = models.CharField(max_length=254, blank=True, null=True, default=None)

    staff = models.ManyToManyField(AUTH_USER_MODEL, through='IssuerStaff')

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=255, blank=True, null=True, default=None)
    #slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)

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
        for member in self.cached_issuerstaff():
            member.cached_user.publish()

    def delete(self, *args, **kwargs):
        if self.recipient_count > 0:
            raise ProtectedError("Issuer can not be deleted because it has previously issued badges.", self)

        # remove any unused badgeclasses owned by issuer
        for bc in self.cached_badgeclasses():
            bc.delete()

        staff = self.cached_issuerstaff()
        ret = super(Issuer, self).delete(*args, **kwargs)

        # remove membership records
        for membership in staff:
            membership.delete(publish_issuer=False)

        if apps.is_installed('badgebook'):
            # badgebook shim
            try:
                from badgebook.models import LmsCourseInfo
                # update LmsCourseInfo's that were using this issuer as the default_issuer
                for course_info in LmsCourseInfo.objects.filter(default_issuer=self):
                    course_info.default_issuer = None
                    course_info.save()
            except ImportError:
                pass

        return ret

    def save(self, *args, **kwargs):
        ret = super(Issuer, self).save(*args, **kwargs)

        # if no owner staff records exist, create one for created_by
        if len(self.owners) < 1 and self.created_by_id:
            IssuerStaff.objects.create(issuer=self, user=self.created_by, role=IssuerStaff.ROLE_OWNER)

        return ret

    def get_absolute_url(self):
        return reverse('issuer_json', kwargs={'entity_id': self.entity_id})

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def jsonld_id(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def editors(self):
        return self.staff.filter(issuerstaff__role__in=(IssuerStaff.ROLE_EDITOR, IssuerStaff.ROLE_OWNER))

    @property
    def owners(self):
        return self.staff.filter(issuerstaff__role=IssuerStaff.ROLE_OWNER)

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuerstaff(self):
        return IssuerStaff.objects.filter(issuer=self)

    @property
    def staff_items(self):
        return self.cached_issuerstaff()

    @staff_items.setter
    def staff_items(self, value):
        """
        Update this issuers IssuerStaff from a list of IssuerStaffSerializerV2 data
        """
        existing_staff_idx = {s.cached_user: s for s in self.staff_items}
        new_staff_idx = {s['cached_user']: s for s in value}

        with transaction.atomic():
            # add missing staff records
            for staff_data in value:
                if staff_data['cached_user'] not in existing_staff_idx:
                    staff_record, created = IssuerStaff.cached.get_or_create(
                        issuer=self,
                        user=staff_data['cached_user'],
                        defaults={
                            'role': staff_data['role']
                        })
                    if not created:
                        staff_record.role = staff_data['role']
                        staff_record.save()

            # remove old staff records -- but never remove the only OWNER role
            for staff_record in self.staff_items:
                if staff_record.cached_user not in new_staff_idx:
                    if staff_record.role != IssuerStaff.ROLE_OWNER or len(self.owners) > 1:
                        staff_record.delete()

    @cachemodel.cached_method(auto_publish=True)
    def cached_editors(self):
        UserModel = get_user_model()
        return UserModel.objects.filter(issuerstaff__issuer=self, issuerstaff__role=IssuerStaff.ROLE_EDITOR)

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        return self.badgeclasses.all()

    def cached_badgeinstances(self):
        return chain(*[bc.cached_badgeinstances() for bc in self.cached_badgeclasses()])

    @cachemodel.cached_method(auto_publish=True)
    def cached_pathways(self):
        return self.pathway_set.filter(is_active=True)

    @cachemodel.cached_method(auto_publish=True)
    def cached_recipient_groups(self):
        return self.recipientgroup_set.all()

    @property
    def recipient_count(self):
        return sum(bc.recipient_count() for bc in self.cached_badgeclasses())

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
            json['image'] = OriginSetting.HTTP + reverse('issuer_image', kwargs={'entity_id': self.entity_id})
        return json

    @property
    def json(self):
        return self.get_json()


class IssuerStaff(cachemodel.CacheModel):
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

    def publish(self):
        super(IssuerStaff, self).publish()
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        publish_issuer = kwargs.pop('publish_issuer', True)
        super(IssuerStaff, self).delete()
        if publish_issuer:
            self.issuer.publish()
        self.user.publish()

    @property
    def cached_user(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(pk=self.user_id)

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)


class BadgeClass(ResizeUploadedImage, ScrubUploadedSvgImage, BaseAuditedModel, BaseVersionedEntity):
    entity_class_name = 'BadgeClass'

    source = models.CharField(max_length=254, default='local')
    source_url = models.CharField(max_length=254, blank=True, null=True, default=None)
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.CASCADE, related_name="badgeclasses")

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=255, blank=True, null=True, default=None)
    #slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)

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

    def delete(self, *args, **kwargs):
        if self.recipient_count() > 0:
            raise ProtectedError("BadgeClass may only be deleted if all BadgeInstances have been revoked.", self)

        if self.pathway_element_count() > 0:
            raise ProtectedError("BadgeClass may only be deleted if all PathwayElementBadge have been removed.", self)

        if len(self.cached_completion_elements()) > 0:
            return ProtectedError("Badge could not be deleted. It is being used as a pathway completion badge.", self)

        issuer = self.issuer
        super(BadgeClass, self).delete(*args, **kwargs)
        issuer.publish()

    def get_absolute_url(self):
        return reverse('badgeclass_json', kwargs={'entity_id': self.entity_id})

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def jsonld_id(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    def get_criteria_url(self):
        if self.criteria_url:
            return self.criteria_url
        return OriginSetting.HTTP+reverse('badgeclass_criteria', kwargs={'entity_id': self.entity_id})

    @property
    def owners(self):
        return self.cached_issuer.owners

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

    def issue(self, recipient_id=None, evidence=None, notify=False, created_by=None, allow_uppercase=False, badgr_app=None):
        return BadgeInstance.objects.create_badgeinstance(
            badgeclass=self, recipient_id=recipient_id, evidence=evidence,
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
            json['image'] = OriginSetting.HTTP + reverse('badgeclass_image', kwargs={'entity_id': self.entity_id})
        return json

    @property
    def json(self):
        return self.get_json()


class BadgeInstance(BaseAuditedModel, BaseVersionedEntity):
    entity_class_name = 'Assertion'

    badgeclass = models.ForeignKey(BadgeClass, blank=False, null=False, on_delete=models.CASCADE, related_name='badgeinstances')
    issuer = models.ForeignKey(Issuer, blank=False, null=False)

    recipient_identifier = models.EmailField(max_length=1024, blank=False, null=False)
    image = models.FileField(upload_to='uploads/badges', blank=True)

    # slug has been deprecated for now, but preserve existing values
    slug = models.CharField(max_length=255, blank=True, null=True, default=None)
    #slug = AutoSlugField(max_length=255, populate_from='get_new_slug', unique=True, blank=False, editable=False)

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

    narrative = models.TextField(blank=True, null=True, default=None)

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
        return OriginSetting.HTTP+reverse('shared_badge', kwargs={'badge_id': self.entity_id})

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
        return reverse('badgeinstance_json', kwargs={'entity_id': self.entity_id})

    @property
    def jsonld_id(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def public_url(self):
        return OriginSetting.HTTP+self.get_absolute_url()

    @property
    def owners(self):
        return self.issuer.owners

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.salt = uuid.uuid4().hex
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
        self.publish_by('entity_id', 'revoked')

    def delete(self, *args, **kwargs):
        badgeclass = self.badgeclass
        recipient_profile = self.cached_recipient_profile
        super(BadgeInstance, self).delete(*args, **kwargs)
        badgeclass.publish()
        if recipient_profile:
            recipient_profile.publish()
        self.publish_delete('entity_id', 'revoked')

    def revoke(self, revocation_reason):
        if self.revoked:
            raise ValidationError("Assertion is already revoked")

        if not revocation_reason:
            raise ValidationError("revocation_reason is required")

        self.revoked = True
        self.revocation_reason = revocation_reason
        self.image.delete()
        self.save()

        # remove BadgeObjectiveAwards from badgebook if needed
        if apps.is_installed('badgebook'):
            try:
                from badgebook.models import BadgeObjectiveAward, LmsCourseInfo
                try:
                    award = BadgeObjectiveAward.cached.get(badge_instance_id=assertion.id)
                except BadgeObjectiveAward.DoesNotExist:
                    pass
                else:
                    award.delete()
            except ImportError:
                pass

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
                'badge_id': self.entity_id,
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
            "uid": self.entity_id,
            "image": OriginSetting.HTTP + reverse('badgeinstance_image', kwargs={'entity_id': self.entity_id}),
            "badge": self.cached_badgeclass.jsonld_id,
            "verify": {
                "url": self.public_url,
                "type": "hosted"
            }
        }

        if self.evidence_url:
            json['evidence'] = self.evidence_url

        json['issuedOn'] = self.created_at.isoformat()

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

    @cachemodel.cached_method(auto_publish=True)
    def cached_evidence(self):
        return self.badgeinstanceevidence_set.all()

    @property
    def evidence(self):
        if hasattr(self, '_evidence_items'):
            return getattr(self, '_evidence_items', [])
        return self.cached_evidence()

    @evidence.setter
    def evidence(self, value):
        """
        Set this assertions badgeinstanceevidence from a list of EvidenceItemSerializerV2 data
        """
        self._evidence_items = value

    @property
    def evidence_url(self):
        """Exists for compliance with ob1.x badges"""
        evidence_list = self.cached_evidence()
        if len(evidence_list) > 1:
            return self.public_url
        if len(evidence_list) == 1:
            return evidence_list[0].evidence_url

    @property
    def evidence_items(self):
        """exists to cajole EvidenceItemSerializer"""
        return self.cached_evidence()


class BadgeInstanceEvidence(cachemodel.CacheModel):
    badgeinstance = models.ForeignKey('issuer.BadgeInstance')
    evidence_url = models.CharField(max_length=2083)
    narrative = models.TextField(blank=True, null=True, default=None)

    def publish(self):
        super(BadgeInstanceEvidence, self).publish()
        self.badgeinstance.publish()

    def delete(self, *args, **kwargs):
        badgeinstance = self.badgeinstance
        ret = super(BadgeInstanceEvidence, self).delete(*args, **kwargs)
        badgeinstance.publish()
        return ret
