from django.db import models
from autoslug import AutoSlugField
from mainsite.utils import generate_entity_uri
from entity.models import BaseVersionedEntity

class Institution(models.Model):
    
    def __str__(self):
        return self.name
    
    name = models.CharField(max_length=512)


class Faculty(BaseVersionedEntity, models.Model):

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'faculties'
        unique_together = ('name', 'institution')

    name = models.CharField(max_length=512)
    institution = models.ForeignKey(Institution, blank=False, null=False)

    def get_institution(self):
        return self.institution