from __future__ import unicode_literals

import base64
import random
import re
import string
from hashlib import md5
from itertools import chain

import cachemodel
import datetime
from allauth.account.models import EmailAddress, EmailConfirmation
from basic_models.models import IsActive
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from oauth2_provider.models import AccessToken, Application
from oauthlib.common import generate_token
from oauthlib.oauth2 import BearerToken
from rest_framework.authtoken.models import Token

from backpack.models import BackpackCollection
from entity.models import BaseVersionedEntity
from issuer.models import Issuer, BadgeInstance, BaseAuditedModel
from badgeuser.managers import CachedEmailAddressManager, BadgeUserManager
from mainsite.models import ApplicationInfo


class CachedEmailAddress(EmailAddress, cachemodel.CacheModel):
    objects = CachedEmailAddressManager()

    class Meta:
        proxy = True
        verbose_name = _("email address")
        verbose_name_plural = _("email addresses")

    def generate_forgot_password_time_cache_key(self):
        return "{}_forgot_request_date".format(self.email)

    def get_last_forgot_password_sent_time(self):
        cached_time = cache.get(self.generate_forgot_password_time_cache_key())
        return cached_time

    def set_last_forgot_password_sent_time(self, new_datetime):
        cache.set(self.generate_forgot_password_time_cache_key(), new_datetime)

    def generate_verification_time_cache_key(self):
        return "{}_verification_request_date".format(self.email)

    def get_last_verification_sent_time(self):
        cached_time = cache.get(self.generate_verification_time_cache_key())
        return cached_time

    def set_last_verification_sent_time(self, new_datetime):
        cache.set(self.generate_verification_time_cache_key(), new_datetime)

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

    @property
    def verified(self):
        return self.canonical_email.verified

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

        if not self.canonical_email.email.lower() == self.email.lower():
            fail("New EmailAddressVariant does not match stored email address.")

        return True


class BadgeUser(BaseVersionedEntity, AbstractUser, cachemodel.CacheModel):
    """
    A full-featured user model that can be an Earner, Issuer, or Consumer of Open Badges
    """
    entity_class_name = 'BadgeUser'

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    badgrapp = models.ForeignKey('mainsite.BadgrApp', blank=True, null=True, default=None)

    marketing_opt_in = models.BooleanField(default=False)

    objects = BadgeUserManager()

    class Meta:
        verbose_name = _('badge user')
        verbose_name_plural = _('badge users')
        db_table = 'users'

    def __unicode__(self):
        return u"{} <{}>".format(self.get_full_name(), self.email)

    def get_full_name(self):
        return u"%s %s" % (self.first_name, self.last_name)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.primary_email], **kwargs)

    def publish(self):
        super(BadgeUser, self).publish()
        self.publish_by('username')

    def delete(self, *args, **kwargs):
        super(BadgeUser, self).delete(*args, **kwargs)
        self.publish_delete('username')

    @cachemodel.cached_method(auto_publish=True)
    def cached_emails(self):
        return CachedEmailAddress.objects.filter(user=self)

    @cachemodel.cached_method(auto_publish=True)
    def cached_backpackcollections(self):
        return BackpackCollection.objects.filter(created_by=self)

    @property
    def email_items(self):
        return self.cached_emails()

    @email_items.setter
    def email_items(self, value):
        """
        Update this users EmailAddress from a list of BadgeUserEmailSerializerV2 data
        :param value: list(BadgeUserEmailSerializerV2)
        :return: None
        """
        if len(value) < 1:
            raise ValidationError("Must have at least 1 email")

        new_email_idx = {d['email']: d for d in value}

        primary_count = sum(1 if d.get('primary', False) else 0 for d in value)
        if primary_count != 1:
            raise ValidationError("Must have exactly 1 primary email")

        with transaction.atomic():
            # add or update existing items
            for email_data in value:
                primary = email_data.get('primary', False)
                emailaddress, created = CachedEmailAddress.cached.get_or_create(
                    email=email_data['email'],
                    defaults={
                        'user': self,
                        'primary': primary
                    })
                if created:
                    # new email address send a confirmation
                    emailaddress.send_confirmation()
                else:
                    if emailaddress.user_id == self.id:
                        # existing email address owned by user
                        emailaddress.primary = primary
                        emailaddress.save()
                    elif not emailaddress.verified:
                        # existing unverified email address, handover to this user
                        emailaddress.user = self
                        emailaddress.primary = primary
                        emailaddress.save()
                        emailaddress.send_confirmation()
                    else:
                        # existing email address used by someone else
                        raise ValidationError("Email '{}' may already be in use".format(email_data.get('email')))

            # remove old items
            for emailaddress in self.email_items:
                if emailaddress.email not in new_email_idx:
                    emailaddress.delete()

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
    def primary_email(self):
        primaries = filter(lambda e: e.primary, self.cached_emails())
        if len(primaries) > 0:
            return primaries[0].email
        return self.email

    @property
    def verified_emails(self):
        return filter(lambda e: e.verified, self.cached_emails())

    @property
    def verified(self):
        if self.is_superuser:
            return True

        if len(self.verified_emails) > 0:
            return True

        return False

    @property
    def all_recipient_identifiers(self):
        return [e.email for e in self.cached_emails() if e.verified] + [e.email for e in self.cached_email_variants()]

    def is_email_verified(self, email):
        if email in self.all_recipient_identifiers:
            return True

        try:
            app_infos = ApplicationInfo.objects.filter(application__user=self)
            if any(app_info.trust_email_verification for app_info in app_infos):
                return True
        except ApplicationInfo.DoesNotExist:
            return False

        return False

    @cachemodel.cached_method(auto_publish=True)
    def cached_issuers(self):
        return Issuer.objects.filter(staff__id=self.id).distinct()

    @property
    def peers(self):
        """
        a BadgeUser is a Peer of another BadgeUser if they appear in an IssuerStaff together
        """
        return set(chain(*[[s.cached_user for s in i.cached_issuerstaff()] for i in self.cached_issuers()]))

    def cached_badgeclasses(self):
        return chain.from_iterable(issuer.cached_badgeclasses() for issuer in self.cached_issuers())

    @cachemodel.cached_method(auto_publish=True)
    def cached_badgeinstances(self):
        return BadgeInstance.objects.filter(recipient_identifier__in=self.all_recipient_identifiers)

    @cachemodel.cached_method(auto_publish=True)
    def cached_externaltools(self):
        return [a.cached_externaltool for a in self.externaltooluseractivation_set.filter(is_active=True)]

    @cachemodel.cached_method(auto_publish=True)
    def cached_token(self):
        user_token, created = \
                Token.objects.get_or_create(user=self)
        return user_token.key

    @cachemodel.cached_method(auto_publish=True)
    def cached_agreed_terms_version(self):
        try:
            return self.termsagreement_set.all().order_by('-terms_version')[0]
        except IndexError:
            pass
        return None

    @property
    def agreed_terms_version(self):
        v = self.cached_agreed_terms_version()
        if v is None:
            return 0
        return v.terms_version

    @agreed_terms_version.setter
    def agreed_terms_version(self, value):
        try:
            value = int(value)
        except ValueError as e:
            return

        if value > self.agreed_terms_version:
            if TermsVersion.active_objects.filter(version=value).exists():
                if not self.pk:
                    self.save()
                self.termsagreement_set.get_or_create(terms_version=value, defaults=dict(agreed=True))

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


class BadgrAccessTokenManager(models.Manager):

    def generate_new_token_for_user(self, user, scope='r:profile', application=None, expires=None, refresh_token=False):
        with transaction.atomic():
            if application is None:
                application, created = Application.objects.get_or_create(
                    client_id='public',
                    client_type=Application.CLIENT_PUBLIC,
                    authorization_grant_type=Application.GRANT_PASSWORD,
                )
                if created:
                    ApplicationInfo.objects.create(application=application)

            if expires is None:
                access_token_expires_seconds = getattr(settings, 'OAUTH2_PROVIDER', {}).get('ACCESS_TOKEN_EXPIRE_SECONDS', 86400)
                expires = timezone.now() + datetime.timedelta(seconds=access_token_expires_seconds)

            accesstoken = self.create(
                application=application,
                user=user,
                expires=expires,
                token=generate_token(),
                scope=scope
            )

        return accesstoken

    def get_from_entity_id(self, entity_id):
        # lookup by a faked
        padding = len(entity_id) % 4
        if padding > 0:
            entity_id = '{}{}'.format(entity_id, (4-padding)*'=')
        decoded = base64.urlsafe_b64decode(entity_id.encode('utf-8'))
        id = re.sub(r'^{}'.format(self.model.fake_entity_id_prefix), '', decoded)
        try:
            pk = int(id)
        except ValueError as e:
            pass
        else:
            try:
                obj = self.get(pk=pk)
            except self.model.DoesNotExist:
                pass
            else:
                return obj
        raise self.model.DoesNotExist


class BadgrAccessToken(AccessToken, cachemodel.CacheModel):
    objects = BadgrAccessTokenManager()
    fake_entity_id_prefix = "BadgrAccessToken.id="

    class Meta:
        proxy = True

    @property
    def entity_id(self):
        # fake an entityId for this non-entity
        digest = "{}{}".format(self.fake_entity_id_prefix, self.pk)
        b64_string = base64.urlsafe_b64encode(digest)
        b64_trimmed = re.sub(r'=+$', '', b64_string)
        return b64_trimmed

    def get_entity_class_name(self):
        return 'AccessToken'

    @property
    def application_name(self):
        return self.application.name

    @property
    def applicationinfo(self):
        try:
            return self.application.applicationinfo
        except ApplicationInfo.DoesNotExist:
            return ApplicationInfo()


class TermsVersionManager(cachemodel.CacheModelManager):
    latest_version_key = "badgr_server_cached_latest_version"

    def latest_version(self):
        latest = self.cached_latest()
        if latest is not None:
            return latest.version
        return 0

    def latest(self):
        try:
            return self.filter(is_active=True).order_by('-version')[0]
        except IndexError:
            pass

    def cached_latest(self):
        latest = cache.get(self.latest_version_key)
        if latest is None:
            return self.publish_latest()
        return latest

    def publish_latest(self):
        latest = self.latest()
        if latest is not None:
            cache.set(self.latest_version_key, latest, timeout=None)
        return latest


class TermsVersion(IsActive, BaseAuditedModel, cachemodel.CacheModel):
    version = models.PositiveIntegerField(unique=True)
    short_description = models.TextField(blank=True)
    cached = TermsVersionManager()

    def publish(self):
        super(TermsVersion, self).publish()
        TermsVersion.cached.publish_latest()


class TermsAgreement(BaseAuditedModel, cachemodel.CacheModel):
    user = models.ForeignKey('badgeuser.BadgeUser')
    terms_version = models.PositiveIntegerField()
    agreed = models.BooleanField(default=True)

    class Meta:
        ordering = ('-terms_version',)
        unique_together = ('user', 'terms_version')
