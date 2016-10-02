from hashlib import md5
from itertools import chain
import random, string

import cachemodel
from allauth.account.models import EmailAddress, EmailConfirmation
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from rest_framework.authtoken.models import Token

from issuer.models import Issuer

from .managers import CachedEmailAddressManager


class CachedEmailAddress(EmailAddress, cachemodel.CacheModel):
    objects = CachedEmailAddressManager()

    class Meta:
        proxy = True
        verbose_name = _("email address")
        verbose_name_plural = _("email addresses")

    def publish(self):
        super(CachedEmailAddress, self).publish()
        self.publish_by('email')
        self.user.publish()

    def delete(self, *args, **kwargs):
        user = self.user
        self.publish_delete('email')
        self.publish_delete('pk')
        super(CachedEmailAddress, self).delete(*args, **kwargs)
        user.publish()

    def set_as_primary(self, conditional=False):
        # shadow parent function, but use CachedEmailAddress manager to ensure cache gets updated
        old_primary = CachedEmailAddress.objects.get_primary(self.user)
        if old_primary:
            if conditional:
                return False
            old_primary.primary = False
            old_primary.save()
        return super(CachedEmailAddress, self).set_as_primary(conditional=conditional)

    def save(self, *args, **kwargs):
        super(CachedEmailAddress, self).save(*args, **kwargs)

        if not self.emailaddressvariant_set.exists() and self.email != self.email.lower():
            self.add_variant(self.email.lower())

    @cachemodel.cached_method(auto_publish=True)
    def cached_variants(self):
        return self.emailaddressvariant_set.all()

    def add_variant(self, email_variation):
        existing_variants = EmailAddressVariant.objects.filter(
            canonical_email=self, email=email_variation
        )
        if email_variation not in [e.email for e in existing_variants.all()]:
            return EmailAddressVariant.objects.create(
                canonical_email=self, email=email_variation
            )
        else:
            raise ValidationError("Email variant {} already exists".format(email_variation))

class ProxyEmailConfirmation(EmailConfirmation):
    class Meta:
        proxy = True
        verbose_name = _("email confirmation")
        verbose_name_plural = _("email confirmations")


class EmailAddressVariant(models.Model):
    email = models.EmailField(blank=False)
    canonical_email = models.ForeignKey(CachedEmailAddress, blank=False)

    def save(self, *args, **kwargs):
        self.is_valid(raise_exception=True)

        super(EmailAddressVariant, self).save(*args, **kwargs)
        self.canonical_email.save()

    def __unicode__(self):
        return self.email

    def is_valid(self, raise_exception=False):
        def fail(message):
            if raise_exception:
                raise ValidationError(message)
            else:
                self.error = message
                return False

        if not self.canonical_email_id:
            try:
                self.canonical_email = CachedEmailAddress.cached.get(email=self.email)
            except CachedEmailAddress.DoesNotExist:
                fail("Canonical Email Address not found")

        if not self.canonical_email.verified:
            fail("EmailAddress must be verified before registering variants.")

        if not self.canonical_email.email.lower() == self.email.lower():
            fail("New EmailAddressVariant does not match stored email address.")

        return True


class BadgeUser(AbstractUser, cachemodel.CacheModel):
    """
    A full-featured user model that can be an Earner, Issuer, or Consumer of Open Badges
    """

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('badge user')
        verbose_name_plural = _('badge users')
        db_table = 'users'

    def __unicode__(self):
        return self.email

    def get_absolute_url(self):
        return reverse('user_detail', kwargs={'user_id': self.pk})

    def get_full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email], **kwargs)

    def publish(self):
        super(BadgeUser, self).publish()
        self.publish_by('username')

    def delete(self, *args, **kwargs):
        super(BadgeUser, self).delete(*args, **kwargs)
        self.publish_delete('username')

    @cachemodel.cached_method(auto_publish=True)
    def cached_emails(self):
        return CachedEmailAddress.objects.filter(user=self)

    def cached_email_variants(self):
        return chain.from_iterable(email.cached_variants() for email in self.cached_emails())

    def can_add_variant(self, email):
        try:
            canonical_email = CachedEmailAddress.objects.get(email=email, user=self, verified=True)
        except CachedEmailAddress.DoesNotExist:
            return False

        if email != canonical_email.email \
                and email not in [e.email for e in canonical_email.cached_variants()] \
                and EmailAddressVariant(email=email, canonical_email=canonical_email).is_valid():
            return True
        return False

    @property
    def all_recipient_identifiers(self):
        return [e.email for e in self.cached_emails() if e.verified] + [e.email for e in self.cached_email_variants()]

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return Issuer.objects.filter( Q(owner__id=self.id) | Q(staff__id=self.id) ).distinct()

    def cached_badgeclasses(self):
        return chain.from_iterable(issuer.cached_badgeclasses() for issuer in self.cached_issuers())

    @cachemodel.cached_method(auto_publish=True)
    def cached_token(self):
        user_token, created = \
                Token.objects.get_or_create(user=self)
        return user_token.key

    def replace_token(self):
        Token.objects.filter(user=self).delete()
        # user_token, created = \
        #         Token.objects.get_or_create(user=self)
        self.save()
        return self.cached_token()

    def save(self, *args, **kwargs):
        if not self.username:
            # md5 hash the email and then encode as base64 to take up only 25 characters
            hashed = md5(self.email + ''.join(random.choice(string.lowercase) for i in range(64))).digest().encode('base64')[:-1]  # strip last character because its a newline
            self.username = "badgr{}".format(hashed[:25])

        if getattr(settings, 'BADGEUSER_SKIP_LAST_LOGIN_TIME', True):
            # skip saving last_login to the database
            if 'update_fields' in kwargs and kwargs['update_fields'] is not None and 'last_login' in kwargs['update_fields']:
                kwargs['update_fields'].remove('last_login')
                if len(kwargs['update_fields']) < 1:
                    # nothing to do, abort so we dont call .publish()
                    return
        return super(BadgeUser, self).save(*args, **kwargs)
