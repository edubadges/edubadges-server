import cachemodel
from django.db import models
from entity.models import BaseVersionedEntity, EntityUserProvisionmentMixin
from mainsite.models import BaseAuditedModel
from mainsite.mixins import ImageUrlGetterMixin
from staff.mixins import PermissionedModelMixin
from staff.models import FacultyStaff, InstitutionStaff


class Institution(EntityUserProvisionmentMixin, PermissionedModelMixin, ImageUrlGetterMixin, BaseVersionedEntity, BaseAuditedModel):
    
    def __str__(self):
        return self.name

    identifier = models.CharField(max_length=255, unique=True, null=True)
    name = models.CharField(max_length=255, unique=True)
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.InstitutionStaff", related_name='+')
    description = models.TextField(blank=True, null=True, default=None)
    image = models.FileField(upload_to='uploads/institution', blank=True, null=True)
    grading_table = models.CharField(max_length=254, blank=True, null=True, default=None)
    brin = models.CharField(max_length=254, blank=True, null=True, default=None)

    @property
    def children(self):
        return self.cached_faculties()

    def get_faculties(self, user, permissions):
        return [fac for fac in self.cached_faculties() if fac.has_permissions(user, permissions)]

    @property
    def assertions(self):
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
        return list(self.faculty_set.all())

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        r = []
        for faculty in self.cached_faculties():
            r += list(faculty.issuer_set.all())
        return r

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r += list(issuer.cached_badgeclasses())
        return r

    def create_staff_membership(self, user, permissions):
        try:
            staff = InstitutionStaff.objects.get(user=user)
            for key in permissions.keys():
                value = permissions[key]
                setattr(staff, key, value)
            staff.save()
        except InstitutionStaff.DoesNotExist:
            return InstitutionStaff.objects.create(user=user, institution=self, **permissions)


class Faculty(EntityUserProvisionmentMixin, PermissionedModelMixin, BaseVersionedEntity, BaseAuditedModel):

    def __str__(self):
        return self.name

    def __unicode__(self):
        return '{}'.format(self.name)

    class Meta:
        verbose_name_plural = 'faculties'
        unique_together = ('name', 'institution')

    name = models.CharField(max_length=512)
    institution = models.ForeignKey(Institution, on_delete=models.CASCADE, blank=False, null=False)
    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.FacultyStaff")
    description = models.TextField(blank=True, null=True, default=None)

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
        assertions = []
        for issuer in self.issuers:
            assertions += issuer.assertions
        return assertions

    @property
    def issuers(self):
        return self.issuer_set.all()

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return FacultyStaff.objects.filter(faculty=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return self.issuers

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r.append(issuer.cached_badgeclasses())
        return r
