from django.conf import settings
from django.db import models

from component_store.models import Issuer, BadgeClass, BadgeInstance


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class SaveComponent(models.Model):
    pass
    #  def save(self, *args, **kwargs):
    #      # TODO: Who calls this?
    #      if not self.pk and not self.url:
    #          self.url = self.get_url()

    #      super(AbstractStoredComponent, self).save(*args, **kwargs)

    #  def get_url(self):
    #      # TODO: Who calls this?
    #      return self.json.get('id')


class LocalIssuer(Issuer):
    pass
    #  @classmethod
    #  def from_analyzed_instance(cls, abi, **kwargs):
    #      # TODO: Who calls this?
    #      pass


class LocalBadgeClass(BadgeClass):
    pass
    #  @classmethod
    #  def from_analyzed_instance(cls, abi, **kwargs):
    #      # TODO: Who calls this?
    #      pass


class LocalBadgeInstance(BadgeInstance):
    pass
    #  recipient_user = models.ForeignKey(AUTH_USER_MODEL, null=True)
    #  recipient_id = models.CharField(max_length=1024, blank=False)

    #  def image_url(self):
    #      if getattr(settings, 'MEDIA_URL').startswith('http'):
    #          return getattr(settings, 'MEDIA_URL') \
    #              + self.image.name
    #      else:
    #          return getattr(settings, 'HTTP_ORIGIN') \
    #              + getattr(settings, 'MEDIA_URL') \
    #              + self.image.name

    #  @classmethod
    #  def from_analyzed_instance(cls, abi, **kwargs):
    #      pass
