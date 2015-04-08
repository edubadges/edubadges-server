import datetime
import json
import uuid

from django.conf import settings
from django.core.mail import send_mail
from django.db import models
import django.template.loader

from autoslug import AutoSlugField
import cachemodel
from jsonfield import JSONField

from mainsite.utils import slugify

from .utils import bake, generate_sha256_hashstring


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

    # Subclasses must implement 'slug' as a field
    def get_slug(self):
        if self.slug is None or self.slug == '':
            # If there isn't a slug, object has been initialized but not saved,
            # so this change will be saved later in present process; fine not to save now.
            self.slug = slugify(self.name)
        return self.slug

    def get_full_url(self):
        return str(getattr(settings, 'HTTP_ORIGIN')) + self.get_absolute_url()

    # Handle updating json in case initial slug guess was modified on save because of a uniqueness constraint
    def process_real_full_url(self):
        self.json['id'] = self.get_full_url()

    def save(self):
        super(Component, self).save()

        # Make adjustments if the slug has changed due to uniqueness constraint
        object_id = self.json.get('id')
        if object_id != self.get_full_url():
            self.process_real_full_url()
            super(Component, self).save()

    # Quick getter for values stored in the json
    def prop(self, property_name):
        return self.json.get(property_name)


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
        return "/public/issuers/%s" % self.get_slug()


class IssuerStaff(models.Model):
    issuer = models.ForeignKey(Issuer)
    badgeuser = models.ForeignKey(AUTH_USER_MODEL)
    editor = models.BooleanField(default=False)


class BadgeClass(Component):
    """
    Open Badges Specification BadgeClass object
    """
    issuer = models.ForeignKey(Issuer, blank=False, null=False, on_delete=models.PROTECT, related_name="badgeclasses")
    name = models.CharField(max_length=255)
    slug = AutoSlugField(max_length=255, populate_from='name', unique=True, blank=False, editable=True)
    criteria_text = models.TextField(blank=True, null=True)  # TODO: CKEditor field
    image = models.ImageField(upload_to='uploads/badges', blank=True)

    @property
    def owner(self):
        return self.issuer.owner

    # TODO: Here's the replacement for criteria_url
    @property
    def criteria_url(self):
        return self.json.get('criteria')

    def get_absolute_url(self):
        return "/public/badges/%s" % self.get_slug()

    def process_real_full_url(self):
        self.json['image'] = self.get_full_url() + '/image'
        if self.json.get('criteria') is None or self.json.get('criteria') == '':
            self.json['criteria'] = self.get_full_url() + '/criteria'

        super(BadgeClass, self).process_real_full_url()


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
    image = models.ImageField(upload_to='issued/badges', blank=True)
    revoked = models.BooleanField(default=False)
    revocation_reason = models.CharField(max_length=255, blank=True, null=True, default=None)

    @property
    def owner(self):
        return self.issuer.owner

    def get_absolute_url(self):
        return "/public/assertions/%s" % self.get_slug()

    def get_new_slug(self):
        return str(uuid.uuid4())

    def get_slug(self):
        if self.slug is None or self.slug == '':
            self.slug = self.get_new_slug()
        return self.slug

    def save(self, *args, **kwargs):
        if self.pk is None:
            salt = self.get_new_slug()
            self.json['recipient']['salt'] = salt
            self.json['recipient']['identity'] = generate_sha256_hashstring(self.email, salt)

            self.created_at = datetime.datetime.now()
            self.json['issuedOn'] = self.created_at.isoformat()

            self.image = bake(self.badgeclass.image, json.dumps(self.json, indent=2))
            self.image.open()

        if self.revoked is False:
            self.revocation_reason = None
        # Don't need to worry about id uniqueness, so can skip immediate super's save method.
        super(Component, self).save(*args, **kwargs)

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
                'issuer_name': self.issuer.name,
                'issuer_url': self.issuer.prop('url'),
                'image_url': self.get_full_url() + '/image'
            }
        except KeyError as e:
            # for when a property isn't stored right in a json
            raise e

        t = django.template.loader.get_template('issuer/notify_earner_email.txt')
        ht = django.template.loader.get_template('issuer/notify_earner_email.html')
        text_output_message = t.render(email_context)
        html_output_message = ht.render(email_context)
        mail_meta = {
            'subject': 'Congratulations, you earned a badge!',
            # 'from_address': email_context['issuer_name'] + ' Badges <noreply@oregonbadgealliance.org>',
            'from_address': 'Oregon Badge Alliance' + ' Badges <noreply@oregonbadgealliance.org>',
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
