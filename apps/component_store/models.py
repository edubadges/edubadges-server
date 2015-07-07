import uuid

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from autoslug import AutoSlugField
import cachemodel
from jsonfield import JSONField


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Component(cachemodel.CacheModel):
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


class Issuer(Component):
    """
    Open Badges Specification IssuerOrg object
    """
    owner = models.ForeignKey(AUTH_USER_MODEL, related_name='owner',
                              on_delete=models.PROTECT, null=False)

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


class BadgeClass(Component):
    """
    Open Badges Specification BadgeClass object
    """
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.PROTECT, related_name="badgeclasses")

    criteria_text = models.TextField(blank=True, null=True)  # TODO: CKEditor field
    image = models.ImageField(upload_to='uploads/badges', blank=True)
    name = models.CharField(max_length=255)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)

    class Meta:
        verbose_name_plural = "Badge classes"

    def get_absolute_url(self):
        return reverse('badgeclass_json', kwargs={'slug': self.slug})


class BadgeInstance(Component):
    """
    Open Badges Specification Assertion object
    """
    badgeclass = models.ForeignKey(
        BadgeClass,
        blank=False,
        null=False,
        on_delete=models.PROTECT,
        related_name='assertions'
    )  # null=True in cred_store
    issuer = models.ForeignKey(Issuer, blank=False, null=False)  # null=True in cred_store

    email = models.EmailField(max_length=255, blank=False, null=False)
    image = models.ImageField(upload_to='uploads/badges', blank=True)  # upload_to='issued' in cred_store
    slug = AutoSlugField(max_length=255, populate_from='populate_slug', unique=True, blank=False, editable=False)

    def __unicode__(self):
        return "%s issued to %s" % (self.badgeclass.name, self.email,)

    def get_absolute_url(self):
        return reverse('badgeinstance_json', kwargs={'slug': self.slug})

    def populate_slug(self):
        return str(uuid.uuid4())
