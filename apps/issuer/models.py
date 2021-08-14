import datetime
import io
import logging
import os
import uuid
from collections import OrderedDict
from json import dumps as json_dumps
from json import loads as json_loads
from urllib.parse import urljoin

import cachemodel
import requests
from django.apps import apps
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction, IntegrityError
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from jsonfield import JSONField
from openbadges_bakery import bake
from rest_framework import serializers

from directaward.models import DirectAward, DirectAwardBundle
from entity.models import BaseVersionedEntity, EntityUserProvisionmentMixin
from issuer.managers import BadgeInstanceManager, IssuerManager, BadgeClassManager, BadgeInstanceEvidenceManager
from mainsite.exceptions import BadgrValidationError, BadgrValidationFieldError, BadgrValidationMultipleFieldError
from mainsite.mixins import ImageUrlGetterMixin, DefaultLanguageMixin
from mainsite.models import BadgrApp, BaseAuditedModel, ArchiveMixin
from mainsite.utils import OriginSetting, generate_entity_uri, EmailMessageMaker
from signing import tsob
from signing.models import AssertionTimeStamp, PublicKeyIssuer
from signing.models import PublicKey
from staff.mixins import PermissionedModelMixin
from staff.models import BadgeClassStaff, IssuerStaff
from .utils import generate_sha256_hashstring, CURRENT_OBI_VERSION, get_obi_context, add_obi_version_ifneeded, \
    UNVERSIONED_BAKED_VERSION

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
logger = logging.getLogger('Badgr.Debug')


class OriginalJsonMixin(models.Model):
    original_json = models.TextField(blank=True, null=True, default=None)

    class Meta:
        abstract = True

    def get_original_json(self):
        if self.original_json:
            try:
                return json_loads(self.original_json)
            except (TypeError, ValueError) as e:
                pass

    def get_filtered_json(self, excluded_fields=()):
        original = self.get_original_json()
        if original is not None:
            return {key: original[key] for key in [k for k in list(original.keys()) if k not in excluded_fields]}


class BaseOpenBadgeObjectModel(OriginalJsonMixin, cachemodel.CacheModel):
    source = models.CharField(max_length=254, default='local')
    source_url = models.CharField(max_length=254, blank=True, null=True, default=None)

    class Meta:
        abstract = True

    def get_extensions_manager(self):
        raise NotImplementedError()

    @cachemodel.cached_method(auto_publish=True)
    def cached_extensions(self):
        return self.get_extensions_manager().all()

    @property
    def extension_items(self):
        return {e.name: json_loads(e.original_json) for e in self.cached_extensions()}

    @extension_items.setter
    def extension_items(self, value):
        if value is None:
            value = {}
        touched_idx = []

        with transaction.atomic():
            if not self.pk and value:
                self.save()

            # add new
            for ext_name, ext in list(value.items()):
                ext_json = json_dumps(ext)
                ext, ext_created = self.get_extensions_manager().get_or_create(name=ext_name, defaults=dict(
                    original_json=ext_json
                ))
                if not ext_created:
                    ext.original_json = ext_json
                    ext.save()
                touched_idx.append(ext.pk)

            # remove old
            for extension in self.cached_extensions():
                if extension.pk not in touched_idx:
                    extension.delete()


class BaseOpenBadgeExtension(cachemodel.CacheModel):
    name = models.CharField(max_length=254)
    original_json = models.TextField(blank=True, null=True, default=None)

    def __unicode__(self):
        return self.name

    class Meta:
        abstract = True


class Issuer(EntityUserProvisionmentMixin,
             ArchiveMixin,
             PermissionedModelMixin,
             ImageUrlGetterMixin,
             BaseAuditedModel,
             DefaultLanguageMixin,
             BaseVersionedEntity,
             BaseOpenBadgeObjectModel):
    entity_class_name = 'Issuer'
    DUTCH_NAME = "issuer"

    staff = models.ManyToManyField('badgeuser.BadgeUser', through='staff.IssuerStaff')
    badgrapp = models.ForeignKey('mainsite.BadgrApp', on_delete=models.SET_NULL, blank=True, null=True, default=None)
    name_english = models.CharField(max_length=512, null=True)  # either this name,
    name_dutch = models.CharField(max_length=512, null=True)  # or this one, must be supplied to pass save() method
    image_english = models.FileField(upload_to='uploads/issuers', blank=True, null=True)
    image_dutch = models.FileField(upload_to='uploads/issuers', blank=True, null=True)
    description_english = models.TextField(blank=True, null=True, default=None)
    description_dutch = models.TextField(blank=True, null=True, default=None)
    url_english = models.CharField(max_length=254, blank=True, null=True, default=None)
    url_dutch = models.CharField(max_length=254, blank=True, null=True, default=None)
    email = models.CharField(max_length=254, blank=True, null=True, default=None)
    old_json = JSONField()
    objects = IssuerManager()
    cached = cachemodel.CacheModelManager()
    faculty = models.ForeignKey('institution.Faculty', on_delete=models.CASCADE, blank=False, null=False)

    @property
    def description(self):
        return self.return_value_according_to_language(self.description_english, self.description_dutch)

    @property
    def name(self):
        return self.return_value_according_to_language(self.name_english, self.name_dutch)

    @property
    def image(self):
        image = self.return_value_according_to_language(self.image_english, self.image_dutch)
        if not image:
            return self.institution.image
        return image

    @property
    def url(self):
        return self.return_value_according_to_language(self.url_english, self.url_dutch)

    def get_report(self):
        total_assertions_formal = 0
        total_assertions_informal = 0
        total_assertions_revoked = 0
        total_enrollments = 0
        unique_recipients = set()
        for badgeclass in self.cached_badgeclasses():
            for assertion in badgeclass.cached_assertions():
                if badgeclass.formal:
                    total_assertions_formal += 1
                else:
                    total_assertions_informal += 1
                if assertion.revoked:
                    total_assertions_revoked += 1
                unique_recipients.add(assertion.user)
            total_enrollments += badgeclass.cached_enrollments().__len__()
        return {'name': self.name,
                'type': self.__class__.__name__.capitalize(),
                'id': self.pk,
                'total_badgeclasses': self.cached_badgeclasses().__len__(),
                'total_enrollments': total_enrollments,
                'total_recipients': unique_recipients.__len__(),
                'total_assertions_formal': total_assertions_formal,
                'total_assertions_informal': total_assertions_informal,
                'total_assertions_revoked': total_assertions_revoked}

    def validate_unique(self, exclude=None):
        if not self.archived:
            if self.name_dutch and self.name_english:
                query = Q(name_english=self.name_english) | Q(name_dutch=self.name_dutch)
            elif self.name_english:
                query = Q(name_english=self.name_english)
            elif self.name_dutch:
                query = Q(name_english=self.name_english)
            else:
                raise BadgrValidationMultipleFieldError([
                    ['name_english', 'Either Dutch or English name is required', 913],
                    ['name_dutch', 'Either Dutch or English name is required', 913]
                ])
            issuer_same_name = self.__class__.objects \
                .filter(query,
                        faculty=self.faculty,
                        archived=False) \
                .exclude(pk=self.pk).first()
            if issuer_same_name:
                name_english_the_same = issuer_same_name.name_english == self.name_english and bool(
                    issuer_same_name.name_english)
                name_dutch_the_same = issuer_same_name.name_dutch == self.name_dutch and bool(
                    issuer_same_name.name_dutch)
                both_the_same = name_english_the_same and name_dutch_the_same
                if both_the_same:
                    raise BadgrValidationMultipleFieldError([
                        ['name_english', "There is already an Issuer with this English name inside this Issuer group",
                         908],
                        ['name_dutch', "There is already an Issuer with this Dutch name inside this Issuer group", 914]
                    ])
                elif name_dutch_the_same:
                    raise BadgrValidationFieldError('name_dutch',
                                                    "There is already an Issuer with this Dutch name inside this Issuer group",
                                                    914)
                elif name_english_the_same:
                    raise BadgrValidationFieldError('name_english',
                                                    "There is already an Issuer with this English name inside this Issuer group",
                                                    908)
        return super(Issuer, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        if not self.name_english and not self.name_dutch:
            raise BadgrValidationError('Either English or Dutch name must be supplied', 999)
        self.validate_unique()
        return super(Issuer, self).save(*args, **kwargs)

    @property
    def parent(self):
        return self.faculty

    @property
    def children(self):
        return self.cached_badgeclasses()

    @property
    def assertions(self):
        """return all assertions, also assertions belonging to archived entities
        this is used to check if an entity can be archived / deleted
        """
        assertions = []
        for bc in self.badgeclasses.all():
            assertions += bc.assertions
        return assertions

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return list(IssuerStaff.objects.filter(issuer=self))

    def create_staff_membership(self, user, permissions):
        return IssuerStaff.objects.create(user=user, issuer=self, **permissions)

    def get_badgeclasses(self, user, permissions):
        return [bc for bc in self.cached_badgeclasses() if bc.has_permissions(user, permissions)]

    @property
    def badgeclasses_count(self):
        return BadgeClass.objects.filter(issuer=self,
                                         archived=False).count()

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        return list(self.badgeclasses.filter(archived=False))

    @cachemodel.cached_method(auto_publish=True)
    def cached_assertions(self):
        r = []
        for bc in self.cached_badgeclasses():
            r += bc.cached_assertions()
        return r

    @cachemodel.cached_method(auto_publish=True)
    def cached_pending_enrollments(self):
        r = []
        for bc in self.cached_badgeclasses():
            r += bc.cached_pending_enrollments()
        return r

    def get_absolute_url(self):
        return reverse('issuer_json', kwargs={'entity_id': self.entity_id})

    def get_url_with_public_key(self, public_key_issuer):
        if public_key_issuer.issuer != self:
            raise ValueError('Public key issuer does not belong to this Issuer.')
        return self.jsonld_id + '/pubkey/{}'.format(public_key_issuer.entity_id)

    def create_empty_key_address(self):
        """
        Creates a PublicKeyIssuer instance which has a public api url address. This address is needed at the time
        of timestamping and filled with a PublicKey at the time of signing.
        :return: PublicKeyIssuer instance
        """
        obj = PublicKeyIssuer.objects.create(issuer=self)
        return obj

    @property
    def institution(self):
        if self.faculty:
            return self.faculty.institution
        return None

    @property
    def public_url(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def jsonld_id(self):
        if self.source_url:
            return self.source_url
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def owners(self):
        return self.get_local_staff_members(
            ['may_create', 'may_read', 'may_update', 'may_delete', 'may_award', 'may_administrate_users'])

    @property
    def current_signers(self):
        return [staff for staff in self.staff_items if staff.is_signer]

    def get_extensions_manager(self):
        return self.issuerextension_set

    @property
    def image_preview(self):
        return self.image

    def create_private_key(self, password, symmetric_key):
        symmetric_key.validate_password(password)
        return tsob.create_new_private_key(password, symmetric_key, self)

    def get_json(self, obi_version=CURRENT_OBI_VERSION, include_extra=True, use_canonical_id=False, signed=False,
                 public_key_issuer=None, expand_public_key=False, expand_institution=False, expand_awards=False):
        if signed and not public_key_issuer:
            raise ValueError(
                'Cannot return signed issuer json without knowing which public key address is going to be used.')
        if public_key_issuer:
            if public_key_issuer.issuer != self:
                raise ValueError('Public key issuer does not belong to this issuer.')
        obi_version, context_iri = get_obi_context(obi_version)

        json = OrderedDict({'@context': context_iri})
        # For spec compliance we also need the non-language properties
        json.update(OrderedDict(
            type='Issuer',
            name=self.name,
            name_english=self.name_english,
            name_dutch=self.name_dutch,
            url=self.url,
            url_english=self.url_english,
            url_dutch=self.url_dutch,
            email=self.email,
            description=self.description,
            description_english=self.description_english,
            description_dutch=self.description_dutch,
        ))
        if not signed:
            json['id'] = self.jsonld_id if use_canonical_id else add_obi_version_ifneeded(self.jsonld_id, obi_version)
        elif signed:
            json['id'] = self.get_url_with_public_key(public_key_issuer)

        if self.image:
            image_url = OriginSetting.HTTP + reverse('issuer_image', kwargs={'entity_id': self.entity_id})
            json['image'] = image_url
            if self.image_english:
                json['image_english'] = f"{image_url}?lang=en"
            if self.image_dutch:
                json['image_dutch'] = f"{image_url}?lang=nl"
            if self.original_json:
                image_info = self.get_original_json().get('image', None)
                if isinstance(image_info, dict):
                    json['image'] = image_info
                    json['image']['id'] = image_url

        # source url
        if self.source_url:
            if obi_version == '1_1':
                json["source_url"] = self.source_url
                json["hosted_url"] = OriginSetting.HTTP + self.get_absolute_url()
            elif obi_version == '2_0':
                json["sourceUrl"] = self.source_url
                json["hostedUrl"] = OriginSetting.HTTP + self.get_absolute_url()

        # extensions
        if len(self.cached_extensions()) > 0:
            for extension in self.cached_extensions():
                json[extension.name] = json_loads(extension.original_json)

        # institution extensions
        if self.faculty:
            if self.faculty.institution.brin:
                json['extensions:InstitutionIdentifierExtension'] = {
                    "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/InstitutionIdentifierExtension/context.json",
                    "type": ["Extension", "extensions:InstitutionIdentifierExtension"],
                    "InstitutionIdentifier": self.faculty.institution.brin
                }
            if self.faculty.institution.grading_table:
                json['extensions:GradingTableExtension'] = {
                    "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/GradingTableExtension/context.json",
                    "type": ["Extension", "extensions:GradingTableExtension"],
                    "GradingTableURL": self.faculty.institution.grading_table
                }
            if self.faculty.institution.name:
                json['extensions:InstitutionNameExtension'] = {
                    "@context": f"{settings.EXTENSIONS_ROOT_URL}/extensions/InstitutionNameExtension/context.json",
                    "type": ["Extension", "extensions:InstitutionNameExtension"],
                    "InstitutionName": self.faculty.institution.name
                }

        if expand_institution:
            if not self.faculty:
                raise ValueError('issuer is not assigned to a faculty')
            if not self.faculty.institution:
                raise ValueError('issuer is not assigned to an institution')
            json['faculty'] = {'name': self.faculty.name,
                               'name_english': self.faculty.name_english,
                               'name_dutch': self.faculty.name_dutch,
                               'institution': self.faculty.institution.get_json(obi_version=CURRENT_OBI_VERSION,
                                                                                expand_awards=expand_awards)}

        # pass through imported json
        if include_extra:
            extra = self.get_filtered_json()
            if extra is not None:
                for k, v in list(extra.items()):
                    if k not in json:
                        json[k] = v

        try:
            if signed:
                json['verification'] = {"type": "SignedBadge", "creator": public_key_issuer.public_url}
                if expand_public_key:
                    json['publicKey'] = public_key_issuer.get_json()
                else:
                    json['publicKey'] = public_key_issuer.public_url
        except PublicKey.DoesNotExist:
            pass
        return json

    @property
    def json(self):
        return self.get_json()

    def get_filtered_json(self,
                          excluded_fields=('@context', 'id', 'type', 'name', 'url', 'description', 'image', 'email')):
        return super(Issuer, self).get_filtered_json(excluded_fields=excluded_fields)

    @property
    def cached_badgrapp(self):
        id = self.badgrapp_id if self.badgrapp_id else getattr(settings, 'BADGR_APP_ID', 1)
        return BadgrApp.cached.get(id=id)

    def __unicode__(self):
        return self.name


class BadgeClass(EntityUserProvisionmentMixin,
                 ArchiveMixin,
                 PermissionedModelMixin,
                 ImageUrlGetterMixin,
                 BaseAuditedModel,
                 DefaultLanguageMixin,
                 BaseVersionedEntity,
                 BaseOpenBadgeObjectModel):
    entity_class_name = 'BadgeClass'
    DUTCH_NAME = "badge class"
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.CASCADE, related_name="badgeclasses")
    name = models.CharField(max_length=255)
    image = models.FileField(upload_to='uploads/badges', blank=True)
    description = models.TextField(blank=True, null=True, default=None)
    criteria_url = models.CharField(max_length=254, blank=True, null=True, default=None)
    criteria_text = models.TextField(blank=True, null=True)
    formal = models.BooleanField(default=False)
    is_private = models.BooleanField(default=False)
    narrative_required = models.BooleanField(default=False)
    evidence_required = models.BooleanField(default=False)
    old_json = JSONField()
    objects = BadgeClassManager()
    cached = cachemodel.CacheModelManager()
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.BadgeClassStaff")
    expiration_period = models.DurationField(null=True)
    award_allowed_institutions = models.ManyToManyField('institution.Institution', blank=True,
                                                        help_text='Allow awards to this institutions')

    class Meta:
        verbose_name_plural = "Badge classes"

    def get_report(self):
        total_assertions_formal = 0
        total_assertions_informal = 0
        total_assertions_revoked = 0
        unique_recipients = set()
        for assertion in self.cached_assertions():
            if self.formal:
                total_assertions_formal += 1
            else:
                total_assertions_informal += 1
            if assertion.revoked:
                total_assertions_revoked += 1
            unique_recipients.add(assertion.user)
        return {'name': self.name,
                'type': self.__class__.__name__.capitalize(),
                'id': self.pk,
                'total_recipients': unique_recipients.__len__(),
                'total_enrollments': self.cached_enrollments().__len__(),
                'total_assertions_formal': total_assertions_formal,
                'total_assertions_informal': total_assertions_informal,
                'total_assertions_revoked': total_assertions_revoked}

    def validate_unique(self, exclude=None):
        if not self.archived:
            if self.__class__.objects \
                    .filter(name=self.name, issuer=self.issuer, archived=False) \
                    .exclude(pk=self.pk) \
                    .exists():
                raise IntegrityError("Badgeclass with this name already exists in the same issuer.")
        return super(BadgeClass, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(BadgeClass, self).save(*args, **kwargs)

    @property
    def institution(self):
        if self.issuer:
            return self.issuer.institution

    @property
    def parent(self):
        return self.issuer

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return BadgeClassStaff.objects.filter(badgeclass=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_assertions(self):
        return list(self.badgeinstances.all())

    @cachemodel.cached_method(auto_publish=True)
    def cached_direct_awards(self):
        return list(DirectAward.objects.filter(badgeclass=self))

    @cachemodel.cached_method(auto_publish=True)
    def cached_pending_direct_awards(self):
        return DirectAward.objects.filter(badgeclass=self, status=DirectAward.STATUS_UNACCEPTED)

    @cachemodel.cached_method(auto_publish=True)
    def cached_direct_award_bundles(self):
        return list(DirectAwardBundle.objects.filter(badgeclass=self))

    @property
    def assertions(self):
        """return all assertions this is used to check if an entity can be archived / deleted"""
        return self.cached_assertions()

    def publish(self):
        super(BadgeClass, self).publish()
        self.issuer.publish()

    def _get_terms(self):
        terms = self.institution.cached_terms()
        if not terms:
            raise ValueError(f"Institution {self.institution.identifier} has no terms. This is required.")
        if self.formal:
            return [term for term in terms if term.terms_type == term.__class__.TYPE_FORMAL_BADGE][0]
        return [term for term in terms if term.terms_type == term.__class__.TYPE_INFORMAL_BADGE][0]

    def terms_accepted(self, user):
        '''returns true if the user accepted the required terms'''
        terms = self._get_terms()
        return terms.has_been_accepted_by(user)

    def accept_terms(self, user):
        '''accepts the required terms for user'''
        terms = self._get_terms()
        return terms.accept(user)

    def get_absolute_url(self):
        return reverse('badgeclass_json', kwargs={'entity_id': self.entity_id})

    def get_url_with_public_key(self, public_key_issuer):
        if public_key_issuer.issuer != self.issuer:
            raise ValueError('Public key issuer does not belong to this Issuer.')
        return self.jsonld_id + '/pubkey/{}'.format(public_key_issuer.entity_id)

    def create_staff_membership(self, user, permissions):
        return BadgeClassStaff.objects.create(user=user, badgeclass=self, **permissions)

    @property
    def public_url(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def jsonld_id(self):
        if self.source_url:
            return self.source_url
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def issuer_jsonld_id(self):
        return self.cached_issuer.jsonld_id

    def get_criteria_url(self):
        if self.criteria_url:
            return self.criteria_url
        return OriginSetting.HTTP + reverse('badgeclass_criteria', kwargs={'entity_id': self.entity_id})

    @property
    def description_nonnull(self):
        return self.description if self.description else ""

    @description_nonnull.setter
    def description_nonnull(self, value):
        self.description = value

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @cachemodel.cached_method(auto_publish=True)
    def cached_enrollments(self):
        from lti_edu.models import StudentsEnrolled
        return StudentsEnrolled.objects.filter(badge_class=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_pending_enrollments(self):
        from lti_edu.models import StudentsEnrolled
        return StudentsEnrolled.objects.filter(badge_class=self, badge_instance=None)

    @property
    def assertions_count(self):
        return BadgeInstance.objects.filter(badgeclass=self,
                                            revoked=False,
                                            acceptance='Accepted').count()

    @cachemodel.cached_method(auto_publish=True)
    def cached_alignments(self):
        return self.badgeclassalignment_set.all()

    @property
    def alignment_items(self):
        return self.cached_alignments()

    @alignment_items.setter
    def alignment_items(self, value):
        if value is None:
            value = []
        keys = ['target_name', 'target_url', 'target_description', 'target_framework', 'target_code']

        def _identity(align):
            """build a unique identity from alignment json"""
            return "&".join("{}={}".format(k, align.get(k, None)) for k in keys)

        def _obj_identity(alignment):
            """build a unique identity from alignment json"""
            return "&".join("{}={}".format(k, getattr(alignment, k)) for k in keys)

        existing_idx = {_obj_identity(a): a for a in self.alignment_items}
        new_idx = {_identity(a): a for a in value}

        with transaction.atomic():
            # HACKY, but force a save to self otherwise we can't create related objects here
            if not self.pk:
                self.save()

            # add missing records
            for align in value:
                if _identity(align) not in existing_idx:
                    alignment = self.badgeclassalignment_set.create(**align)

            # remove old records
            for alignment in self.alignment_items:
                if _obj_identity(alignment) not in new_idx:
                    alignment.delete()

    @cachemodel.cached_method(auto_publish=True)
    def cached_tags(self):
        return self.badgeclasstag_set.all()

    @property
    def tag_items(self):
        return self.cached_tags()

    @tag_items.setter
    def tag_items(self, value):
        if value is None:
            value = []
        existing_idx = [t.name for t in self.tag_items]
        new_idx = value

        with transaction.atomic():
            if not self.pk:
                self.save()

            # add missing
            for t in value:
                if t not in existing_idx:
                    tag = self.badgeclasstag_set.create(name=t)

            # remove old
            for tag in self.tag_items:
                if tag.name not in new_idx:
                    tag.delete()

    def get_extensions_manager(self):
        return self.badgeclassextension_set

    def issue(self, recipient, created_by=None, allow_uppercase=False, extensions=None, send_email=True,
              enforce_validated_name=True, include_evidence=True, **kwargs):
        if not recipient.validated_name and enforce_validated_name:
            raise serializers.ValidationError('You need a validated_name from an Institution to issue badges.')
        assertion = BadgeInstance.objects.create(
            badgeclass=self, recipient_identifier=recipient.get_recipient_identifier(), created_by=created_by,
            allow_uppercase=allow_uppercase, include_evidence=include_evidence,
            user=recipient, extensions=extensions,
            **kwargs
        )
        message = EmailMessageMaker.create_earned_badge_mail(assertion)
        if send_email:
            recipient.email_user(subject='Congratulations, you earned an edubadge!', html_message=message)
        return assertion

    def issue_signed(self, recipient, created_by=None, allow_uppercase=False, signer=None, extensions=None, **kwargs):
        perms = self.get_permissions(signer)
        if not perms['may_sign']:
            raise serializers.ValidationError('You do not have permission to sign badges for this badgeclass.')
        assertion = BadgeInstance.objects.create(
            badgeclass=self, recipient_identifier=recipient.get_recipient_identifier(),
            created_by=created_by, allow_uppercase=allow_uppercase,
            user=recipient, extensions=extensions, **kwargs
        )
        assertion.submit_for_timestamping(signer=signer)
        return assertion

    def get_json(self, obi_version=CURRENT_OBI_VERSION, include_extra=True, use_canonical_id=False, signed=False,
                 public_key_issuer=None):
        if not public_key_issuer and signed:
            raise ValueError(
                'Cannot returned signed version of json without knowing which public key address was used.')
        obi_version, context_iri = get_obi_context(obi_version)
        json = OrderedDict({'@context': context_iri})
        json.update(OrderedDict(
            type='BadgeClass',

            name=self.name,
            description=self.description_nonnull,

        ))

        if not signed:
            json['id'] = self.jsonld_id if use_canonical_id else add_obi_version_ifneeded(self.jsonld_id, obi_version)
            json['issuer'] = self.cached_issuer.jsonld_id if use_canonical_id else add_obi_version_ifneeded(
                self.cached_issuer.jsonld_id, obi_version)
        if signed:
            json['id'] = self.get_url_with_public_key(public_key_issuer)
            json['issuer'] = self.issuer.get_url_with_public_key(public_key_issuer)

        # image
        if self.image:
            image_url = OriginSetting.HTTP + reverse('badgeclass_image', kwargs={'entity_id': self.entity_id})
            json['image'] = image_url
            if self.original_json:
                original_json = self.get_original_json()
                if original_json is not None:
                    image_info = original_json.get('image', None)
                    if isinstance(image_info, dict):
                        json['image'] = image_info
                        json['image']['id'] = image_url

        # criteria
        if obi_version == '1_1':
            json["criteria"] = self.get_criteria_url()
        elif obi_version == '2_0':
            json["criteria"] = {}
            if self.criteria_url:
                json['criteria']['id'] = self.criteria_url
            if self.criteria_text:
                json['criteria']['narrative'] = self.criteria_text

        # source_url
        if self.source_url:
            if obi_version == '1_1':
                json["source_url"] = self.source_url
                json["hosted_url"] = OriginSetting.HTTP + self.get_absolute_url()
            elif obi_version == '2_0':
                json["sourceUrl"] = self.source_url
                json["hostedUrl"] = OriginSetting.HTTP + self.get_absolute_url()

        # alignment / tags
        if obi_version == '2_0':
            json['alignment'] = [a.get_json(obi_version=obi_version) for a in self.cached_alignments()]
            json['tags'] = list(t.name for t in self.cached_tags())

        # extensions
        if len(self.cached_extensions()) > 0:
            for extension in self.cached_extensions():
                json[extension.name] = json_loads(extension.original_json)

        # pass through imported json
        if include_extra:
            extra = self.get_filtered_json()
            if extra is not None:
                for k, v in list(extra.items()):
                    if k not in json:
                        json[k] = v
        return json

    @property
    def json(self):
        return self.get_json()

    def get_filtered_json(self, excluded_fields=(
            '@context', 'id', 'type', 'name', 'description', 'image', 'criteria', 'issuer')):
        return super(BadgeClass, self).get_filtered_json(excluded_fields=excluded_fields)

    @property
    def cached_badgrapp(self):
        return self.cached_issuer.cached_badgrapp


class BadgeInstance(BaseAuditedModel,
                    ImageUrlGetterMixin,
                    BaseVersionedEntity,
                    BaseOpenBadgeObjectModel):
    entity_class_name = 'Assertion'

    issued_on = models.DateTimeField(blank=False, null=False, default=timezone.now)

    public_key_issuer = models.ForeignKey('signing.PublicKeyIssuer', on_delete=models.PROTECT, null=True, default=None)

    identifier = models.CharField(max_length=255, null=True, default=None)  # the uuid used to ID signed assertions

    badgeclass = models.ForeignKey(BadgeClass, blank=False, null=False, on_delete=models.PROTECT,
                                   related_name='badgeinstances')
    issuer = models.ForeignKey(Issuer, on_delete=models.PROTECT, blank=False, null=False)
    user = models.ForeignKey('badgeuser.BadgeUser', blank=True, null=True, on_delete=models.CASCADE)

    RECIPIENT_TYPE_EMAIL = 'email'
    RECIPIENT_TYPE_ID = 'openBadgeId'
    RECIPIENT_TYPE_TELEPHONE = 'telephone'
    RECIPIENT_TYPE_URL = 'url'
    RECIPIENT_TYPE_EDUID = 'id'
    RECIPIENT_TYPE_CHOICES = (
        (RECIPIENT_TYPE_EMAIL, 'email'),
        (RECIPIENT_TYPE_ID, 'openBadgeId'),
        (RECIPIENT_TYPE_TELEPHONE, 'telephone'),
        (RECIPIENT_TYPE_URL, 'url'),
        (RECIPIENT_TYPE_EDUID, 'id'),
    )
    recipient_type = models.CharField(max_length=255, choices=RECIPIENT_TYPE_CHOICES, default=RECIPIENT_TYPE_EDUID,
                                      blank=False, null=False)

    AWARD_TYPE_REQUESTED = 'requested'
    AWARD_TYPE_DIRECT_AWARD = 'direct_award'
    AWARD_TYPE_CHOICES = (
        (AWARD_TYPE_REQUESTED, 'requested'),
        (AWARD_TYPE_DIRECT_AWARD, 'direct_award'),
    )
    award_type = models.CharField(max_length=255, choices=AWARD_TYPE_CHOICES, default=AWARD_TYPE_REQUESTED,
                                  blank=False, null=False)

    direct_award_bundle = models.ForeignKey('directaward.DirectAwardBundle', blank=True, null=True, on_delete=models.PROTECT)

    recipient_identifier = models.CharField(max_length=512, blank=False, null=False, db_index=True)

    image = models.FileField(upload_to='uploads/badges', blank=True, null=True, db_index=True)

    revoked = models.BooleanField(default=False)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)

    expires_at = models.DateTimeField(blank=True, null=True, default=None)

    ACCEPTANCE_UNACCEPTED = 'Unaccepted'
    ACCEPTANCE_ACCEPTED = 'Accepted'
    ACCEPTANCE_REJECTED = 'Rejected'
    ACCEPTANCE_CHOICES = (
        (ACCEPTANCE_UNACCEPTED, 'Unaccepted'),
        (ACCEPTANCE_ACCEPTED, 'Accepted'),
        (ACCEPTANCE_REJECTED, 'Rejected'),
    )
    acceptance = models.CharField(max_length=254, choices=ACCEPTANCE_CHOICES, default=ACCEPTANCE_UNACCEPTED)
    narrative = models.TextField(blank=True, null=True, default=None)

    hashed = models.BooleanField(default=True)
    salt = models.CharField(max_length=254, blank=True, null=True, default=None, db_index=True)

    old_json = JSONField()

    signature = models.TextField(blank=True, null=True, default=None)

    public = models.BooleanField(default=False)

    include_evidence = models.BooleanField(default=False)

    objects = BadgeInstanceManager()
    cached = cachemodel.CacheModelManager()

    class Meta:
        index_together = (
            ('recipient_identifier', 'badgeclass', 'revoked'),
        )

    def validate(self):
        data = {'profile': {'id': self.recipient_identifier}, 'data': self.get_json()}
        response = requests.post(json=data,
                                 url=urljoin(settings.VALIDATOR_URL, 'results'),
                                 headers={'Accept': 'application/json'})
        return response.json()

    @property
    def extended_json(self):
        extended_json = self.json
        extended_json['badge'] = self.badgeclass.json
        extended_json['badge']['issuer'] = self.issuer.json

        return extended_json

    @property
    def share_url(self):
        return self.public_url
        # return OriginSetting.HTTP+reverse('backpack_shared_assertion', kwargs={'share_hash': self.entity_id})

    @property
    def cached_issuer(self):
        return Issuer.cached.get(pk=self.issuer_id)

    @property
    def cached_badgeclass(self):
        return BadgeClass.cached.get(pk=self.badgeclass_id)

    @cachemodel.cached_method(auto_publish=True)
    def cached_evidence(self):
        return self.badgeinstanceevidence_set.all()

    def get_absolute_url(self):
        return reverse('badgeinstance_json', kwargs={'entity_id': self.entity_id})

    @property
    def student_url(self):
        return urljoin(settings.UI_URL, f"details/{self.entity_id}")

    def get_permissions(self, user):
        """
        Function that equates permission for this BadgeInstance to that of the BadgeClass it belongs to.
        Used in HasObjectPermission
        """
        return self.badgeclass.get_permissions(user)

    @property
    def jsonld_id(self):
        if self.source_url:
            return self.source_url
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def badgeclass_jsonld_id(self):
        return self.cached_badgeclass.jsonld_id

    @property
    def issuer_jsonld_id(self):
        return self.cached_issuer.jsonld_id

    @property
    def public_url(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def signing_in_progress(self):
        return not self.signature and self.public_key_issuer

    def submit_for_timestamping(self, signer):
        timestamp = AssertionTimeStamp(badge_instance=self, signer=signer)
        timestamp.submit_assertion()

    def get_recipient_name(self):
        if self.user:
            return self.user.validated_name
        else:
            return None

    def get_email_address(self):
        if self.user:
            return self.user.primary_email
        else:
            return None

    def save(self, *args, **kwargs):
        created = False
        if self.pk is None:
            created = True
            self.salt = uuid.uuid4().hex
            self.created_at = datetime.datetime.now()

            # do this now instead of in AbstractVersionedEntity.save() so we can use it for image name
            if self.entity_id is None:
                self.entity_id = generate_entity_uri()

            if not self.image:
                badgeclass_name, ext = os.path.splitext(self.badgeclass.image.file.name)
                new_image = io.BytesIO()
                bake(image_file=self.cached_badgeclass.image.file,
                     assertion_json_string=json_dumps(self.get_json(obi_version=UNVERSIONED_BAKED_VERSION), indent=2),
                     output_file=new_image)
                self.image.save(name='assertion-{id}{ext}'.format(id=self.entity_id, ext=ext),
                                content=ContentFile(new_image.read()),
                                save=False)

            try:
                from badgeuser.models import CachedEmailAddress
                email_address = self.get_email_address()
                existing_email = CachedEmailAddress.cached.get_student_email(email_address)
                if email_address != existing_email.email and \
                        email_address not in [e.email for e in existing_email.cached_variants()]:
                    existing_email.add_variant(email_address)
            except CachedEmailAddress.DoesNotExist:
                pass

        if self.revoked is False:
            self.revocation_reason = None

        super(BadgeInstance, self).save(*args, **kwargs)
        self.badgeclass.remove_cached_data(['cached_assertions'])
        self.user.remove_cached_data(['cached_badgeinstances'])

    def rebake(self, obi_version=CURRENT_OBI_VERSION, save=True, signature=None, replace_image=False):
        if self.source_url:
            # dont rebake imported assertions
            return

        new_image = io.BytesIO()
        if not signature:
            bake(
                image_file=self.cached_badgeclass.image.file,
                assertion_json_string=json_dumps(self.get_json(obi_version=obi_version), indent=2),
                output_file=new_image
            )
        else:
            bake(
                image_file=self.cached_badgeclass.image.file,
                assertion_json_string=signature,
                output_file=new_image
            )

        new_name = default_storage.save(self.image.name, ContentFile(new_image.read()))
        if not replace_image:
            self.image.name = new_name
        if replace_image:
            self.image.delete()
            self.image.name = new_name
        if save:
            self.save()

    def publish(self):
        super(BadgeInstance, self).publish()
        self.badgeclass.publish()
        if self.user:
            self.user.publish()

        self.publish_by('entity_id', 'revoked')

    def delete(self, *args, **kwargs):
        badgeclass = self.badgeclass
        super(BadgeInstance, self).delete(*args, **kwargs)
        badgeclass.publish()
        if self.user:
            self.user.publish()
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
                    award = BadgeObjectiveAward.cached.get(badge_instance_id=self.id)
                except BadgeObjectiveAward.DoesNotExist:
                    pass
                else:
                    award.delete()
            except ImportError:
                pass

    def get_extensions_manager(self):
        return self.badgeinstanceextension_set

    def get_hashed_identity(self):
        return generate_sha256_hashstring(self.recipient_identifier.lower(), self.salt)

    def get_json(self, obi_version=CURRENT_OBI_VERSION, expand_badgeclass=False, expand_issuer=False,
                 include_extra=True, use_canonical_id=False, signed=False, public_key_issuer=None):

        if signed:
            if expand_issuer != True or expand_badgeclass != True:
                raise ValueError('Must expand issuer and badgeclass if signed is set to true.')
            if not public_key_issuer:
                raise ValueError('Must add a public key issuer object (address) if signed is set to true.')
            if public_key_issuer.issuer != self.issuer:
                raise ValueError('Public key issuer objects does not match assertion issuer')

        obi_version, context_iri = get_obi_context(obi_version)

        json = OrderedDict([
            ('@context', context_iri),
            ('type', 'Assertion'),
        ])

        if signed:
            json['id'] = self.identifier
        else:
            json['id'] = add_obi_version_ifneeded(self.jsonld_id, obi_version)
            json['badge'] = add_obi_version_ifneeded(self.cached_badgeclass.jsonld_id, obi_version)

        image_url = OriginSetting.HTTP + reverse('badgeinstance_image', kwargs={'entity_id': self.entity_id})
        json['image'] = image_url
        if self.original_json:
            image_info = self.get_original_json().get('image', None)
            if isinstance(image_info, dict):
                json['image'] = image_info
                json['image']['id'] = image_url

        if expand_badgeclass:
            json['badge'] = self.cached_badgeclass.get_json(obi_version=obi_version, include_extra=include_extra)
            if signed:
                json['badge']['id'] = self.cached_badgeclass.get_url_with_public_key(public_key_issuer)
            if expand_issuer:
                json['badge']['issuer'] = self.cached_issuer.get_json(obi_version=obi_version,
                                                                      include_extra=include_extra, signed=signed,
                                                                      expand_public_key=False,
                                                                      public_key_issuer=public_key_issuer,
                                                                      expand_institution=True)

        if self.revoked:
            return OrderedDict([
                ('@context', context_iri),
                ('type', 'Assertion'),
                ('id', self.jsonld_id if use_canonical_id else add_obi_version_ifneeded(self.jsonld_id, obi_version)),
                ('revoked', self.revoked),
                ('revocationReason', self.revocation_reason if self.revocation_reason else "")
            ])

        if obi_version == '1_1':
            json["uid"] = self.entity_id
            json["verify"] = {
                "url": self.public_url if use_canonical_id else add_obi_version_ifneeded(self.public_url, obi_version),
                "type": "hosted"
            }
        elif obi_version == '2_0':
            if signed:
                json["verification"] = {
                    "type": "SignedBadge",
                    "creator": public_key_issuer.public_url
                }
            else:
                json["verification"] = {
                    "type": "HostedBadge"
                }

        # evidence
        json['evidence'] = [e.get_json(obi_version) for e in self.cached_evidence()] if self.include_evidence else []

        # narrative
        if self.narrative and obi_version == '2_0':
            json['narrative'] = self.narrative

        # source url
        if self.source_url:
            if obi_version == '1_1':
                json["source_url"] = self.source_url
                json["hosted_url"] = OriginSetting.HTTP + self.get_absolute_url()
            elif obi_version == '2_0':
                json["sourceUrl"] = self.source_url
                json["hostedUrl"] = OriginSetting.HTTP + self.get_absolute_url()

        # issuedOn / expires
        json['issuedOn'] = self.issued_on.isoformat()
        json['updatedAt'] = self.updated_at.isoformat() if self.updated_at else self.created_at.isoformat()
        if self.expires_at:
            json['expires'] = self.expires_at.isoformat()

        # recipient
        if self.hashed:
            json['recipient'] = {
                "hashed": True,
                "type": self.recipient_type,
                "identity": self.get_hashed_identity()
            }
            if self.salt:
                json['recipient']['salt'] = self.salt
        else:
            json['recipient'] = {
                "hashed": False,
                "type": self.recipient_type,
                "identity": self.recipient_identifier
            }

        # extensions
        if len(self.cached_extensions()) > 0:
            for extension in self.cached_extensions():
                json[extension.name] = json_loads(extension.original_json)
        if self.pk is None:
            for extension in self.badgeclass.badgeclassextension_set.all():
                json[extension.name] = json_loads(extension.original_json)
        # pass through imported json
        if include_extra:
            extra = self.get_filtered_json()
            if extra is not None:
                for k, v in list(extra.items()):
                    if k not in json:
                        json[k] = v

        return json

    @property
    def json(self):
        return self.get_json()

    def get_filtered_json(self, excluded_fields=(
            '@context', 'id', 'type', 'uid', 'recipient', 'badge', 'issuedOn', 'image', 'revoked', 'revocationReason',
            'verify',
            'verification')):
        return super(BadgeInstance, self).get_filtered_json(excluded_fields=excluded_fields)

    @property
    def cached_badgrapp(self):
        return self.cached_issuer.cached_badgrapp

    def get_baked_image_url(self, obi_version=CURRENT_OBI_VERSION):
        if obi_version == UNVERSIONED_BAKED_VERSION:
            # requested version is the one referenced in assertion.image
            return self.image.url

        try:
            baked_image = BadgeInstanceBakedImage.cached.get(badgeinstance=self, obi_version=obi_version)
        except BadgeInstanceBakedImage.DoesNotExist:
            # rebake
            baked_image = BadgeInstanceBakedImage(badgeinstance=self, obi_version=obi_version)

            json_to_bake = self.get_json(
                obi_version=obi_version,
                expand_issuer=True,
                expand_badgeclass=True,
                include_extra=True
            )
            badgeclass_name, ext = os.path.splitext(self.badgeclass.image.file.name)
            new_image = io.StringIO()
            bake(image_file=self.cached_badgeclass.image.file,
                 assertion_json_string=json_dumps(json_to_bake, indent=2),
                 output_file=new_image)
            baked_image.image.save(
                name='assertion-{id}-{version}{ext}'.format(id=self.entity_id, ext=ext, version=obi_version),
                content=ContentFile(new_image.read()),
                save=False
            )
            baked_image.save()

        return baked_image.image.url


class BadgeInstanceEvidence(OriginalJsonMixin, cachemodel.CacheModel):
    badgeinstance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE)
    evidence_url = models.CharField(max_length=2083, blank=True, null=True, default=None)
    narrative = models.TextField(blank=True, null=True, default=None)
    name = models.CharField(max_length=255, blank=True, null=True, default=None)
    description = models.TextField(blank=True, null=True, default=None)

    objects = BadgeInstanceEvidenceManager()

    def publish(self):
        super(BadgeInstanceEvidence, self).publish()
        self.badgeinstance.publish()

    def get_json(self, obi_version=CURRENT_OBI_VERSION, include_context=False):
        json = OrderedDict()
        if include_context:
            obi_version, context_iri = get_obi_context(obi_version)
            json['@context'] = context_iri

        json['type'] = 'Evidence'
        if self.evidence_url:
            json['id'] = self.evidence_url
        if self.narrative:
            json['narrative'] = self.narrative
        if self.name:
            json['name'] = self.name
        if self.description:
            json['description'] = self.description
        return json


def _baked_badge_instance_filename_generator(instance, filename):
    return "baked/{version}/{filename}".format(
        version=instance.obi_version,
        filename=filename
    )


class BadgeInstanceBakedImage(cachemodel.CacheModel):
    badgeinstance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE)
    obi_version = models.CharField(max_length=254)
    image = models.FileField(upload_to=_baked_badge_instance_filename_generator, blank=True)

    def publish(self):
        self.publish_by('badgeinstance', 'obi_version')
        return super(BadgeInstanceBakedImage, self).publish()

    def delete(self, *args, **kwargs):
        self.publish_delete('badgeinstance', 'obi_version')
        return super(BadgeInstanceBakedImage, self).delete(*args, **kwargs)


class BadgeClassAlignment(OriginalJsonMixin, cachemodel.CacheModel):
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    target_name = models.TextField()
    target_url = models.CharField(max_length=2083)
    target_description = models.TextField(blank=True, null=True, default=None)
    target_framework = models.TextField(blank=True, null=True, default=None)
    target_code = models.TextField(blank=True, null=True, default=None)

    def publish(self):
        super(BadgeClassAlignment, self).publish()
        self.badgeclass.publish()

    def delete(self, *args, **kwargs):
        super(BadgeClassAlignment, self).delete(*args, **kwargs)
        self.badgeclass.publish()

    def get_json(self, obi_version=CURRENT_OBI_VERSION, include_context=False):
        json = OrderedDict()
        if include_context:
            obi_version, context_iri = get_obi_context(obi_version)
            json['@context'] = context_iri

        json['targetName'] = self.target_name
        json['targetUrl'] = self.target_url
        if self.target_description:
            json['targetDescription'] = self.target_description
        if self.target_framework:
            json['targetFramework'] = self.target_framework
        if self.target_code:
            json['targetCode'] = self.target_code

        return json


class BadgeClassTag(cachemodel.CacheModel):
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)
    name = models.CharField(max_length=254, db_index=True)

    def __unicode__(self):
        return self.name

    def publish(self):
        super(BadgeClassTag, self).publish()
        self.badgeclass.publish()

    def delete(self, *args, **kwargs):
        super(BadgeClassTag, self).delete(*args, **kwargs)
        self.badgeclass.publish()


class IssuerExtension(BaseOpenBadgeExtension):
    issuer = models.ForeignKey('issuer.Issuer', on_delete=models.CASCADE)

    def publish(self):
        super(IssuerExtension, self).publish()
        self.issuer.publish()

    def delete(self, *args, **kwargs):
        super(IssuerExtension, self).delete(*args, **kwargs)
        self.issuer.publish()


class BadgeClassExtension(BaseOpenBadgeExtension):
    badgeclass = models.ForeignKey('issuer.BadgeClass', on_delete=models.CASCADE)

    def publish(self):
        super(BadgeClassExtension, self).publish()
        self.badgeclass.publish()

    def delete(self, *args, **kwargs):
        super(BadgeClassExtension, self).delete(*args, **kwargs)
        self.badgeclass.publish()


class BadgeInstanceExtension(BaseOpenBadgeExtension):
    badgeinstance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE)

    def publish(self):
        super(BadgeInstanceExtension, self).publish()
        self.badgeinstance.publish()

    def delete(self, *args, **kwargs):
        super(BadgeInstanceExtension, self).delete(*args, **kwargs)
        self.badgeinstance.publish()
