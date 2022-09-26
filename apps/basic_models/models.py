from django.conf import settings
from django.db import models

from autoslug import AutoSlugField

try:
    from natural_key.mixins import NaturalKey
except ImportError:
    class NaturalKey(object):
        pass

from .managers import ActiveObjectsManager


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class NameSlug(NaturalKey, models.Model):
    name = models.CharField(max_length=255)
    slug = AutoSlugField(unique=True, populate_from='name')

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

    def publish(self):
        super(NameSlug, self).publish()
        self.publish_by('slug')


NameSlug.natural_key_fields = ('slug',)


class CreatedUpdatedBy(models.Model):
    created_by = models.ForeignKey(AUTH_USER_MODEL, null=True, blank=True,
                                   related_name='+',
                                   on_delete=models.SET_NULL)
    updated_by = models.ForeignKey(AUTH_USER_MODEL, null=True, blank=True,
                                   related_name='+',
                                   on_delete=models.SET_NULL)

    class Meta:
        abstract = True


class CreatedUpdatedAt(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TitleBody(models.Model):
    title = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return self.title

    class Meta:
        abstract = True


class IsActive(models.Model):
    is_active = models.BooleanField(default=True)

    objects = models.Manager()
    active_objects = ActiveObjectsManager()

    class Meta:
        abstract = True


class OnlyOneActive(models.Model):

    def save(self, *args, **kwargs):
        super(OnlyOneActive, self).save(*args, **kwargs)
        # If we were made active, deactivate all other instances
        if self.is_active:
            self.__class__.objects.filter(is_active=True).exclude(pk=self.pk) \
                .update(is_active=False)

    class Meta:
        abstract = True
