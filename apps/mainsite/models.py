import abc
import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from autoslug import AutoSlugField
import cachemodel
from jsonfield import JSONField


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class AbstractComponent(cachemodel.CacheModel):
    """
    A base class for Issuer badge objects, those that are part of badges issue
    by users on this system.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True,
                                   related_name="+")

    json = JSONField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def get_full_url(self):
        return settings.HTTP_ORIGIN + self.get_absolute_url()

    def prop(self, property_name):
        return self.json.get(property_name)


class AbstractIssuer(AbstractComponent):
    """
    Open Badges Specification IssuerOrg object
    """
    image = models.ImageField(upload_to='uploads/issuers', blank=True)
    name = models.CharField(max_length=1024)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True,
                         blank=False, editable=True)


    def get_absolute_url(self):
        return reverse('issuer_json', kwargs={'slug': self.slug})

    @property
    def editors(self):
        # TODO Test this:
        return self.staff.filter(issuerstaff__editor=True)

    class Meta:
        abstract = True


class AbstractBadgeClass(AbstractComponent):
    """
    Open Badges Specification BadgeClass object
    """
    #  issuer = models.ForeignKey(Issuer, blank=False, null=False,
    #                             on_delete=models.PROTECT,
    #                             related_name="badgeclasses")

    criteria_text = models.TextField(blank=True, null=True)  # TODO: CKEditor field
    image = models.ImageField(upload_to='uploads/badges', blank=True)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True,
                         blank=False, editable=True)

    class Meta:
        abstract = True
        verbose_name_plural = "Badge classes"

    def get_absolute_url(self):
        return reverse('badgeclass_json', kwargs={'slug': self.slug})


class AbstractBadgeInstance(AbstractComponent):
    """
    Open Badges Specification Assertion object
    """
    # # 0.5 BadgeInstances have no notion of a BadgeClass (null=True)
    # badgeclass = models.ForeignKey(BadgeClass, blank=False, null=False,
    #                                on_delete=models.PROTECT,
    #                                related_name='assertions')
    # # 0.5 BadgeInstances have no notion of a BadgeClass (null=True)
    # issuer = models.ForeignKey(Issuer, blank=False, null=False)

    email = models.EmailField(max_length=255, blank=False, null=False)
    image = models.ImageField(upload_to='uploads/badges', blank=True)  # upload_to='issued' in cred_store
    slug = AutoSlugField(max_length=255, populate_from='populate_slug',
                         unique=True, blank=False, editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return "%s issued to %s" % (self.badgeclass.name, self.email,)

    def get_absolute_url(self):
        return reverse('badgeinstance_json', kwargs={'slug': self.slug})

    def populate_slug(self):
        return str(uuid.uuid4())

    #  def image_url(self):
    #      if getattr(settings, 'MEDIA_URL').startswith('http'):
    #          return getattr(settings, 'MEDIA_URL') \
    #              + self.image.name
    #      else:
    #          return getattr(settings, 'HTTP_ORIGIN') \
    #              + getattr(settings, 'MEDIA_URL') \
    #              + self.image.name
