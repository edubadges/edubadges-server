import re
from collections import OrderedDict

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.urls import reverse

from cachemodel.decorators import cached_method
from entity.models import BaseVersionedEntity, EntityUserProvisionmentMixin
from mainsite.exceptions import BadgrValidationFieldError, BadgrValidationMultipleFieldError
from mainsite.mixins import ImageUrlGetterMixin, DefaultLanguageMixin
from mainsite.models import BaseAuditedModel, ArchiveMixin
from mainsite.utils import OriginSetting
from staff.mixins import PermissionedModelMixin
from staff.models import FacultyStaff, InstitutionStaff


class Institution(EntityUserProvisionmentMixin, PermissionedModelMixin,
                  ImageUrlGetterMixin, BaseVersionedEntity, BaseAuditedModel):

    def __str__(self):
        return self.name or ''

    DUTCH_NAME = "instelling"

    identifier = models.CharField(max_length=255, unique=True, null=True,
                                  help_text="This is the schac_home, must be set when creating")
    name_english = models.CharField(max_length=255, blank=True, null=True, default=None)
    name_dutch = models.CharField(max_length=255, blank=True, null=True, default=None)
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.InstitutionStaff", related_name='+')
    description_english = models.TextField(blank=True, null=True, default=None)
    description_dutch = models.TextField(blank=True, null=True, default=None)
    image_english = models.FileField(upload_to='uploads/institution', blank=True, null=True)
    image_dutch = models.FileField(upload_to='uploads/institution', blank=True, null=True)
    grading_table = models.CharField(max_length=254, blank=True, null=True, default=None)
    brin = models.CharField(max_length=254, blank=True, null=True, default=None)
    direct_awarding_enabled = models.BooleanField(default=False)
    award_allowed_institutions = models.ManyToManyField('self', blank=True, symmetrical=False,
                                                        help_text='Allow awards to this institutions')
    award_allow_all_institutions = models.BooleanField(default=False, help_text='Allow awards to all institutions')
    public_institution = models.BooleanField(default=True, help_text='Set to false to exclude from the catalog')

    lti_enabled = models.BooleanField(default=False, help_text='Set to true to enable LTI for this institution')
    alternative_identifier = models.CharField(max_length=255, blank=True, null=True, default=None,
                                              help_text='An alternative schac_home for the Pilot microcredentials '
                                                        '(e.g. institutionX.tempguestidp.edubadges.nl)')
    eppn_reg_exp_format = models.CharField(max_length=255, blank=True, null=True, default=None,
                                           help_text='A regular expression which defines the EPPN of an institution '
                                                     '(e.g. .*@tempguestidp.edubadges.nl). '
                                                     'For multiple logical OR use the following format:'
                                                     '(.*@university.org|.*@university-sub.org)')
    linkedin_org_identifier = models.CharField(max_length=255, blank=True, null=True, default=None,
                                               help_text='LinkedIn organisation identifier')
    sis_integration_enabled = models.BooleanField(default=False,
                                                  help_text='Set to true to enable SIS integration for this institution')
    micro_credentials_enabled = models.BooleanField(default=False,
                                                    help_text='Set to true to enable Micro-crdentials for this institution')
    ob3_ssi_agent_enabled = models.BooleanField(default=False,
                                                help_text='Set to true to enable OB3 integration for this institution')
    sis_default_user = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.SET_NULL, blank=True, null=True,
                                         default=None,
                                         related_name='sis_institution',
                                         help_text='The edubadges user that will be used for Direct Awards through the '
                                                   'SIS API. Must be an administrator of this institution')
    manage_client_id = models.CharField(max_length=255, blank=True, null=True, default=None,
                                        help_text='OpenConext client_id for token introspection. The secret is '
                                                  'stored in Manage')
    GRONDSLAG_UITVOERING_OVEREENKOMST = 'uitvoering_overeenkomst'
    GRONDSLAG_GERECHTVAARDIGD_BELANG = 'gerechtvaardigd_belang'
    GRONDSLAG_WETTELIJKE_VERPLICHTING = 'wettelijke_verplichting'
    GEEN_GRONDSLAG = None
    GRONDSLAG_CHOICES = (
        (GRONDSLAG_UITVOERING_OVEREENKOMST, 'uitvoering_overeenkomst'),
        (GRONDSLAG_GERECHTVAARDIGD_BELANG, 'gerechtvaardigd_belang'),
        (GRONDSLAG_WETTELIJKE_VERPLICHTING, 'wettelijke_verplichting'),
        (GEEN_GRONDSLAG, None),
    )
    grondslag_formeel = models.CharField(max_length=254, null=True, blank=True, choices=GRONDSLAG_CHOICES,
                                         default=GRONDSLAG_UITVOERING_OVEREENKOMST)
    grondslag_informeel = models.CharField(max_length=254, null=True, blank=True, choices=GRONDSLAG_CHOICES,
                                           default=GRONDSLAG_UITVOERING_OVEREENKOMST)
    TYPE_WO = 'WO'
    TYPE_HBO = 'HBO'
    TYPE_MBO = 'MBO'
    TYPE_CHOICES = (
        (TYPE_WO, 'WO'),
        (TYPE_HBO, 'HBO'),
        (TYPE_MBO, 'MBO'),
    )
    institution_type = models.CharField(max_length=254, null=True, blank=True, choices=TYPE_CHOICES)
    DEFAULT_LANGUAGE_DUTCH = "nl_NL"
    DEFAULT_LANGUAGE_ENGLISH = "en_EN"
    DEFAULT_LANGUAGE_CHOICES = (
        (DEFAULT_LANGUAGE_DUTCH, "nl_NL"),
        (DEFAULT_LANGUAGE_ENGLISH, "en_EN")
    )
    default_language = models.CharField(max_length=254, choices=DEFAULT_LANGUAGE_CHOICES,
                                        default=DEFAULT_LANGUAGE_DUTCH)

    def clean(self):
        if self.eppn_reg_exp_format:
            try:
                re.compile(self.eppn_reg_exp_format)
                if not (self.eppn_reg_exp_format.startswith(".*") or self.eppn_reg_exp_format.startswith("(.*")):
                    raise ValidationError("Eppn reg exp format must start with '.*' or (.*)")
            except re.error as e:
                raise ValidationError(f"Invalid Eppn reg exp format: {e}")

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
                'total_badgeclasss': self.cached_badgeclasses().__len__(),
                'total_issuers': self.cached_issuers().__len__(),
                'total_faculties': self.cached_faculties().__len__(),
                'total_enrollments': total_enrollments,
                'total_recipients': unique_recipients.__len__(),
                'total_admins': [staff for staff in self.cached_staff() if
                                 staff.permissions == staff.full_permissions()].__len__(),
                'total_assertions_formal': total_assertions_formal,
                'total_assertions_informal': total_assertions_informal,
                'total_assertions_revoked': total_assertions_revoked}

    @property
    def name(self):
        return self.return_value_according_to_language(self.name_english, self.name_dutch)

    @property
    def image(self):
        return self.return_value_according_to_language(self.image_english, self.image_dutch)

    @property
    def description(self):
        return self.return_value_according_to_language(self.description_english, self.description_dutch)

    @property
    def children(self):
        return self.cached_faculties()

    def get_faculties(self, user, permissions):
        return [fac for fac in self.cached_faculties() if fac.has_permissions(user, permissions)]

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(Institution, self).save(*args, **kwargs)

    def validate_unique(self, exclude=None):
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
        institution_same_name = self.__class__.objects.filter(query).exclude(pk=self.pk).first()
        if institution_same_name:
            name_english_the_same = institution_same_name.name_english == self.name_english and bool(
                institution_same_name.name_english)
            name_dutch_the_same = institution_same_name.name_dutch == self.name_dutch and bool(
                institution_same_name.name_dutch)
            both_the_same = name_english_the_same and name_dutch_the_same
            if both_the_same:
                raise BadgrValidationMultipleFieldError([
                    ['name_english', "There is already an institution with this English name inside this Issuer group",
                     920],
                    ['name_dutch', "There is already an institution with this Dutch name inside this Issuer group", 919]
                ])
            elif name_dutch_the_same:
                raise BadgrValidationFieldError('name_dutch',
                                                "There is already an institution with this Dutch name inside this Issuer group",
                                                919)
            elif name_english_the_same:
                raise BadgrValidationFieldError('name_english',
                                                "There is already an institution with this English name inside this Issuer group",
                                                920)
        return super(Institution, self).validate_unique(exclude=exclude)

    @property
    def assertions(self):
        """return all assertions, also assertions belonging to archived entities
        this is used to check if an entity can be archived / deleted
        """
        assertions = []
        for faculty in self.faculty_set.all():
            assertions += faculty.assertions
        return assertions

    @cached_method(auto_publish=True)
    def cached_staff(self):
        """returns all staff members"""
        return list(InstitutionStaff.objects.filter(institution=self))

    @cached_method(auto_publish=True)
    def cached_faculties(self):
        return list(self.faculty_set.filter(archived=False))

    @cached_method(auto_publish=True)
    def cached_issuers(self):
        r = []
        for faculty in self.cached_faculties():
            r += list(faculty.cached_issuers())
        return r

    @cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r += list(issuer.cached_badgeclasses())
        return r

    @cached_method()
    def cached_terms(self):
        return list(self.terms.all())

    def create_staff_membership(self, user, permissions):
        try:
            staff = InstitutionStaff.objects.get(user=user)
            for key in permissions.keys():
                value = permissions[key]
                setattr(staff, key, value)
            staff.save()
        except InstitutionStaff.DoesNotExist:
            return InstitutionStaff.objects.create(user=user, institution=self, **permissions)

    def get_json(self, obi_version, expand_awards=False):
        json = OrderedDict()

        image_url = OriginSetting.HTTP + reverse('institution_image', kwargs={'entity_id': self.entity_id})
        # For spec compliance we also need the non-language properties
        json.update(OrderedDict(
            type='Institution',
            name=self.name,
            name_english=self.name_english,
            name_dutch=self.name_dutch,
            entityId=self.entity_id,
            description=self.description,
            description_english=self.description_english,
            description_dutch=self.description_dutch,
            image=image_url,
        ))
        if self.image_english:
            json['image_english'] = f"{image_url}?lang=en"
        if self.image_dutch:
            json['image_dutch'] = f"{image_url}?lang=nl"
        if expand_awards:
            json['award_allow_all_institutions'] = self.award_allow_all_institutions
            json['lti_enabled'] = self.lti_enabled
            json['sis_integration_enabled'] = self.sis_integration_enabled
            json['award_allowed_institutions'] = [inst.name for inst in self.award_allowed_institutions.all()]
        return json


class BadgeClassTag(models.Model):
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, blank=False, null=False)
    name = models.CharField(max_length=254)
    archived = models.BooleanField(default=False, help_text='Set to true to disable this tag from being selectable')

    def __unicode__(self):
        return self.name


class Faculty(EntityUserProvisionmentMixin,
              ArchiveMixin, DefaultLanguageMixin,
              PermissionedModelMixin, BaseVersionedEntity, BaseAuditedModel):

    def __str__(self):
        return self.name or ''

    def __unicode__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name_plural = 'faculties'

    DUTCH_NAME = "issuer group"
    name_dutch = models.CharField(max_length=512, null=True)
    name_english = models.CharField(max_length=512, null=True)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, blank=False, null=False)
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.FacultyStaff")
    description_english = models.TextField(blank=True, null=True, default=None)
    description_dutch = models.TextField(blank=True, null=True, default=None)
    on_behalf_of = models.BooleanField(default=False)
    on_behalf_of_url = models.CharField(max_length=512, blank=True, null=True, default=None)
    on_behalf_of_display_name = models.CharField(max_length=512, blank=True, null=True, default=None)

    @property
    def name(self):
        return self.return_value_according_to_language(self.name_english, self.name_dutch)

    @property
    def description(self):
        return self.return_value_according_to_language(self.description_english, self.description_dutch)

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
                'total_badgeclasss': self.cached_badgeclasses().__len__(),
                'total_issuers': self.cached_issuers().__len__(),
                'total_enrollments': total_enrollments,
                'total_recipients': unique_recipients.__len__(),
                'total_assertions_formal': total_assertions_formal,
                'total_assertions_informal': total_assertions_informal,
                'total_assertions_revoked': total_assertions_revoked}

    def validate_unique(self, exclude=None):
        if not self.archived:
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
                faculty_same_name = self.__class__.objects \
                    .filter(query,
                            institution=self.institution,
                            archived=False) \
                    .exclude(pk=self.pk).first()
                if faculty_same_name:
                    name_english_the_same = faculty_same_name.name_english == self.name_english and bool(
                        faculty_same_name.name_english)
                    name_dutch_the_same = faculty_same_name.name_dutch == self.name_dutch and bool(
                        faculty_same_name.name_dutch)
                    both_the_same = name_english_the_same and name_dutch_the_same
                    if both_the_same:
                        raise BadgrValidationMultipleFieldError([
                            ['name_english',
                             "There is already a Faculty with this English name inside this institution", 917],
                            ['name_dutch', "There is already a Faculty with this Dutch name inside this institution",
                             916]
                        ])
                    elif name_dutch_the_same:
                        raise BadgrValidationFieldError('name_dutch',
                                                        "There is already a Faculty with this Dutch name inside this institution",
                                                        916)
                    elif name_english_the_same:
                        raise BadgrValidationFieldError('name_english',
                                                        "There is already a Faculty with this English name inside this institution",
                                                        917)
        return super(Faculty, self).validate_unique(exclude=exclude)

    def save(self, *args, **kwargs):
        self.validate_unique()
        return super(Faculty, self).save(*args, **kwargs)

    def create_staff_membership(self, user, permissions):
        return FacultyStaff.objects.create(user=user, faculty=self, **permissions)

    def get_issuers(self, user, permissions):
        return [issuer for issuer in self.cached_issuers() if issuer.has_permissions(user, permissions)]

    @property
    def parent(self):
        return self.institution

    @property
    def children(self):
        return self.cached_issuers()

    @property
    def assertions(self):
        """return all assertions, also assertions belonging to archived entities
        this is used to check if an entity can be archived / deleted
        """
        assertions = []
        for issuer in self.issuer_set.all():
            assertions += issuer.assertions
        return assertions

    @cached_method(auto_publish=True)
    def cached_staff(self):
        return FacultyStaff.objects.filter(faculty=self)

    @cached_method(auto_publish=True)
    def cached_issuers(self):
        return list(self.issuer_set.filter(archived=False))

    @cached_method(auto_publish=True)
    def cached_pending_enrollments(self):
        r = []
        for issuer in self.cached_issuers():
            r += issuer.cached_pending_enrollments()
        return r

    @cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            badgeclasses = issuer.cached_badgeclasses()
            if badgeclasses:
                r += badgeclasses
        return r
