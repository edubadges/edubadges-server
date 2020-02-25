import cachemodel
from django.db import models
from entity.models import BaseVersionedEntity
from staff.mixins import PermissionedModelMixin
from staff.models import FacultyStaff, InstitutionStaff

class Institution(PermissionedModelMixin, cachemodel.CacheModel):
    
    def __str__(self):
        return self.name
    
    name = models.CharField(max_length=512)

    staff = models.ManyToManyField('badgeuser.BadgeUser', through="staff.InstitutionStaff")

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
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


class Faculty(PermissionedModelMixin, BaseVersionedEntity, cachemodel.CacheModel):

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

    @property
    def parent(self):
        return self.institution

    @cachemodel.cached_method(auto_publish=True)
    def cached_staff(self):
        return FacultyStaff.objects.filter(faculty=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return list(self.issuer_set.all())

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeclasses(self):
        r = []
        for issuer in self.cached_issuers():
            r.append(issuer.cached_badgeclasses)
        return r

    # needed for the within_scope method of user
    @property
    def faculty(self):
        return self
