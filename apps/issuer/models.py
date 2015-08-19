import datetime
import json
import re
import uuid

from django.conf import settings
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.template.loader import get_template

from autoslug import AutoSlugField
import cachemodel
from jsonfield import JSONField

from bakery import bake

from .utils import generate_sha256_hashstring, badgr_import_url


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class Component(cachemodel.CacheModel):
    """
    A base class for Issuer badge objects, those that are part of badges issue
    by users on this system.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, related_name="+")

    json = JSONField()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def get_full_url(self):
        return settings.HTTP_ORIGIN + self.get_absolute_url()

    def prop(self, property_name):
        try:
            return self.json.get(property_name)
        except Exception:
            return None


class Issuer(Component):
    """
    Open Badges Specification IssuerOrg object
    """
    name = models.CharField(max_length=1024)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)

    owner = models.ForeignKey(AUTH_USER_MODEL, related_name='owner', on_delete=models.PROTECT, null=False)
    staff = models.ManyToManyField(AUTH_USER_MODEL, through='IssuerStaff')

    image = models.ImageField(upload_to='uploads/issuers', blank=True)

    def get_absolute_url(self):
        return reverse('issuer_json', kwargs={'slug': self.slug})

    @property
    def editors(self):
        # TODO Test this:
        return self.staff.filter(issuerstaff__editor=True)


class IssuerStaff(models.Model):
    issuer = models.ForeignKey(Issuer)
    user = models.ForeignKey(AUTH_USER_MODEL)
    editor = models.BooleanField(default=False)

    class Meta:
        unique_together = ('issuer', 'user')


class BadgeClass(Component):
    """
    Open Badges Specification BadgeClass object
    """
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.PROTECT, related_name="badgeclasses")
    name = models.CharField(max_length=255)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)
    criteria_text = models.TextField(blank=True, null=True)  # TODO: CKEditor field
    image = models.ImageField(upload_to='uploads/badges', blank=True)

    class Meta:
        verbose_name_plural = "Badge classes"

    @property
    def owner(self):
        return self.issuer.owner

    @property
    def criteria_url(self):
        return self.json.get('criteria')

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
    )
    email = models.EmailField(max_length=255, blank=False, null=False)
    issuer = models.ForeignKey(Issuer, blank=False, null=False, related_name='assertions')
    slug = AutoSlugField(max_length=255, populate_from='get_new_slug', unique=True, blank=False, editable=False)
    image = models.ImageField(upload_to='issued', blank=True)
    revoked = models.BooleanField(default=False)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)

    def __unicode__(self):
        return "%s issued to %s" % (self.badgeclass.name, self.email,)

    @property
    def owner(self):
        return self.issuer.owner

    @property
    def extended_json(self):
        extended_json = self.json
        extended_json['badge'] = self.badgeclass.json
        extended_json['badge']['issuer'] = self.issuer.json

        return extended_json

    def get_absolute_url(self):
        return reverse('badgeinstance_json', kwargs={'slug': self.slug})

    def get_new_slug(self):
        return str(uuid.uuid4())

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.json['recipient']['salt'] = salt = self.get_new_slug()
            self.json['recipient']['identity'] = generate_sha256_hashstring(self.email, salt)

            self.created_at = datetime.datetime.now()
            self.json['issuedOn'] = self.created_at.isoformat()

            imageFile = default_storage.open(self.badgeclass.image.file.name)
            self.image = bake(imageFile, json.dumps(self.json, indent=2))

            self.image.open()

        if self.revoked is False:
            self.revocation_reason = None

        # TODO: If we don't want AutoSlugField to ensure uniqueness, configure it
        super(BadgeInstance, self).save(*args, **kwargs)

    def notify_earner(self):
        """
        Sends an email notification to the badge earner.
        This process involves creating a badgeanalysis.models.OpenBadge
        returns the EarnerNotification instance.

        TODO: consider making this an option on initial save and having a foreign key to
        the notification model instance (which would link through to the OpenBadge)
        """
        try:
            email_context = {
                'badge_name': self.badgeclass.name,
                'badge_description': self.badgeclass.prop('description'),
                'issuer_name': re.sub(r'[^\w\s]+', '', self.issuer.name, 0, re.I),
                'issuer_url': self.issuer.prop('url'),
                'issuer_image_url': self.issuer.get_full_url() + '/image',
                'image_url': self.get_full_url() + '/image',
                'badgr_import_url': badgr_import_url(self)
            }
        except KeyError as e:
            # A property isn't stored right in json
            raise e

        text_template = get_template('issuer/notify_earner_email.txt')
        html_template = get_template('issuer/notify_earner_email.html')
        text_output_message = text_template.render(email_context)
        html_output_message = html_template.render(email_context)
        mail_meta = {
            'subject': 'Congratulations, you earned a badge!',
            'from_address': '"' + email_context['issuer_name'] + '" <' + getattr(settings, 'DEFAULT_FROM_EMAIL') + '>',
            'to_addresses': [self.email]
        }

        try:
            send_mail(
                mail_meta['subject'],
                text_output_message,
                mail_meta['from_address'],
                mail_meta['to_addresses'],
                fail_silently=False,
                html_message=html_output_message
            )
        except Exception as e:
            raise e
