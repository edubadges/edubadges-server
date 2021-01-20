from collections import OrderedDict
import cachemodel
from django.db import models, IntegrityError
from django.urls import reverse
from entity.models import BaseVersionedEntity, EntityUserProvisionmentMixin
from mainsite.models import BaseAuditedModel, ArchiveMixin
from mainsite.mixins import ImageUrlGetterMixin
from mainsite.utils import OriginSetting
from staff.mixins import PermissionedModelMixin
from staff.models import FacultyStaff, InstitutionStaff


class Institution(EntityUserProvisionmentMixin, PermissionedModelMixin, ImageUrlGetterMixin, BaseVersionedEntity, BaseAuditedModel):
    
    def __str__(self):
        return self.name

    DUTCH_NAME = "instelling"

    identifier = models.CharField(max_length=255, unique=True, null=True, help_text="This is the schac_home, must be set when creating")
    name = models.CharField(max_length=255, unique=True, help_text="Must be set when creating")
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.InstitutionStaff", related_name='+')
    description_english = models.TextField(blank=True, null=True, default=None)
    description_dutch = models.TextField(blank=True, null=True, default=None)
    image = models.FileField(upload_to='uploads/institution', blank=True, null=True)
    grading_table = models.CharField(max_length=254, blank=True, null=True, default=None)
    brin = models.CharField(max_length=254, blank=True, null=True, default=None)
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
    grondslag_formeel = models.CharField(max_length=254, null=True, blank=True, choices=GRONDSLAG_CHOICES, default=GRONDSLAG_UITVOERING_OVEREENKOMST)
    grondslag_informeel = models.CharField(max_length=254, null=True, blank=True, choices=GRONDSLAG_CHOICES, default=GRONDSLAG_UITVOERING_OVEREENKOMST)

    @property
    def children(self):
        return self.cached_faculties()

    def get_faculties(self, user, permissions):
        return [fac for fac in self.cached_faculties() if fac.has_permissions(user, permissions)]

    @property
    def assertions(self):
        """return all assertions, also assertions belonging to archived entities
        this is used to check if an entity can be archived / deleted
        """
        assertions = []
        for faculty in self.faculty_set.all():
            assertions += faculty.assertions
        return assertions

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        """returns all staff members"""
        return list(InstitutionStaff.objects.filter(institution=self))

    @cachemodel.cached_method(auto_publish=True)
    def cached_faculties(self):
        return list(self.faculty_set.filter(archived=False))

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        r = []
        for faculty in self.cached_faculties():
            r += list(faculty.cached_issuers())
        return r

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r += list(issuer.cached_badgeclasses())
        return r

    @cachemodel.cached_method()
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

    def get_json(self, obi_version):
        json = OrderedDict()

        image_url = OriginSetting.HTTP + reverse('institution_image', kwargs={'entity_id': self.entity_id})

        json.update(OrderedDict(
            type='Institution',
            name=self.name,
            entityId=self.entity_id,
            description_english=self.description_english,
            description_dutch=self.description_dutch,
            image=image_url
        ))
        return json


class Faculty(EntityUserProvisionmentMixin,
              ArchiveMixin,
              PermissionedModelMixin, BaseVersionedEntity, BaseAuditedModel):

    def __str__(self):
        return self.name

    def __unicode__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name_plural = 'faculties'

    DUTCH_NAME = "issuer group"
    name = models.CharField(max_length=512)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, blank=False, null=False)
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.FacultyStaff")
    description_english = models.TextField(blank=True, null=True, default=None)
    description_dutch = models.TextField(blank=True, null=True, default=None)

    def validate_unique(self, exclude=None):
        if not self.archived:
            if self.__class__.objects\
                    .filter(name=self.name, institution=self.institution, archived=False)\
                    .exclude(pk=self.pk)\
                    .exists():
                raise IntegrityError("Faculty with this name already exists in the same institution.")
        super(Faculty, self).validate_unique(exclude=exclude)

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

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return FacultyStaff.objects.filter(faculty=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return list(self.issuer_set.filter(archived=False))

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r.append(issuer.cached_badgeclasses())
        return r
