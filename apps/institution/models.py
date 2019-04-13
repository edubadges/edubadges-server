from django.db import models
# from autoslug import AutoSlugField
# from mainsite.managers import SlugOrJsonIdCacheModelManager

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
    
    def get_institution(self):
        return self.institution

#     slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)
#     cached = SlugOrJsonIdCacheModelManager(slug_kwarg_name='id', slug_field_name='id')
