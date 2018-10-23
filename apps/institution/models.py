from django.db import models

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