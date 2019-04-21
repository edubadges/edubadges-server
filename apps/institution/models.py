from django.db import models
from autoslug import AutoSlugField

class Institution(models.Model):
    
    def __str__(self):
        return self.name
    
    name = models.CharField(max_length=512)


class Faculty(models.Model):

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'faculties'

    name = models.CharField(max_length=512)
    institution = models.ForeignKey(Institution, blank=False, null=False)
    entity_id = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True, default=None, null=True)

    def get_institution(self):
        return self.institution

