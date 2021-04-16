import base64
import hmac
import re
import urllib.parse
from datetime import datetime, timedelta
from hashlib import sha1

import cachemodel
from basic_models.models import CreatedUpdatedBy, CreatedUpdatedAt, IsActive
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import models, transaction
from django.db.models import Manager, ProtectedError
from django.urls import reverse
from django.utils.deconstruct import deconstructible
from oauth2_provider.models import AccessToken
from rest_framework.authtoken.models import Token

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class BaseAuditedModel(cachemodel.CacheModel):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.SET_NULL, blank=True, null=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey('badgeuser.BadgeUser', on_delete=models.SET_NULL, blank=True, null=True, related_name="+")

    class Meta:
        abstract = True

    @property
    def cached_creator(self):
        from badgeuser.models import BadgeUser
        return BadgeUser.cached.get(id=self.created_by_id)


class EmailBlacklist(models.Model):
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = 'Blacklisted email'
        verbose_name_plural = 'Blacklisted emails'

    @staticmethod
    def generate_email_signature(email):
        secret_key = settings.UNSUBSCRIBE_SECRET_KEY

        expiration = datetime.utcnow() + timedelta(days=7)  # In one week.
        timestamp = int((expiration - datetime(1970, 1, 1)).total_seconds())

        email_encoded = base64.b64encode(email.encode('utf-8'))
        hashed = hmac.new(secret_key.encode('utf-8'), email_encoded + bytes(str(timestamp), 'utf-8'), sha1)

        return reverse('unsubscribe', kwargs={
            'email_encoded': email_encoded,
            'expiration': timestamp,
            'signature': hashed.hexdigest(),
        })

    @staticmethod
    def verify_email_signature(email_encoded, expiration, signature):
        secret_key = settings.UNSUBSCRIBE_SECRET_KEY

        hashed = hmac.new(secret_key, email_encoded + expiration, sha1)
        return hmac.compare_digest(hashed.hexdigest(), str(signature))


class BadgrAppManager(Manager):
    def get_current(self, request=None, raise_exception=True):
        origin = None
        existing_session_app_id = None

        if request:
            if request.META.get('HTTP_ORIGIN'):
                origin = request.META.get('HTTP_ORIGIN')
            elif request.META.get('HTTP_REFERER'):
                origin = request.META.get('HTTP_REFERER')
            existing_session_app_id = request.session.get('badgr_app_pk', None)

        if origin:
            url = urllib.parse.urlparse(origin)
            try:
                return self.get(cors=url.netloc)
            except self.model.DoesNotExist:
                pass

        if existing_session_app_id:
            try:
                return self.get(id=existing_session_app_id)
            except self.model.DoesNotExist:
                pass
        badgr_app_id = getattr(settings, 'BADGR_APP_ID', None)
        if raise_exception and not badgr_app_id:
            raise ImproperlyConfigured("Must specify a BADGR_APP_ID")
        return self.get(id=badgr_app_id)


class BadgrApp(CreatedUpdatedBy, CreatedUpdatedAt, IsActive, cachemodel.CacheModel):
    name = models.CharField(max_length=254)
    cors = models.CharField(max_length=254, unique=True)
    email_confirmation_redirect = models.URLField()
    signup_redirect = models.URLField()
    forgot_password_redirect = models.URLField()
    ui_login_redirect = models.URLField(null=True)
    ui_signup_success_redirect = models.URLField(null=True)
    ui_connect_success_redirect = models.URLField(null=True)
    public_pages_redirect = models.URLField(null=True)
    oauth_authorization_redirect = models.URLField(null=True)
    use_auth_code_exchange = models.BooleanField(default=False)
    is_demo_environment = models.BooleanField(default=False, blank=True, null=True)
    oauth_application = models.ForeignKey("oauth2_provider.Application", on_delete=models.PROTECT, null=True, blank=True)

    objects = BadgrAppManager()

    def __unicode__(self):
        return self.cors


@deconstructible
class DefinedScopesValidator(object):
    message = "Does not match defined scopes"
    code = 'invalid'

    def __call__(self, value):
        defined_scopes = set(getattr(settings, 'OAUTH2_PROVIDER', {}).get('SCOPES', {}).keys())
        provided_scopes = set(s.strip() for s in re.split(r'[\s\n]+', value))
        if provided_scopes - defined_scopes:
            raise ValidationError(self.message, code=self.code)
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class ApplicationInfo(cachemodel.CacheModel):
    application = models.OneToOneField('oauth2_provider.Application', on_delete=models.CASCADE)
    icon = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=254, blank=True, null=True, default=None)
    website_url = models.URLField(blank=True, null=True, default=None)
    allowed_scopes = models.TextField(blank=False, validators=[DefinedScopesValidator()])
    trust_email_verification = models.BooleanField(default=False)

    def get_visible_name(self):
        if self.name:
            return self.name
        return self.application.name

    def get_icon_url(self):
        if self.icon:
            return self.icon.url

    @property
    def scope_list(self):
        return [s for s in re.split(r'[\s\n]+', self.allowed_scopes) if s]


class AccessTokenProxy(AccessToken):
    class Meta:
        proxy = True
        verbose_name = 'access token'
        verbose_name_plural = 'access tokens'

    def __str__(self):
        return self.obscured_token

    def __unicode__(self):
        return self.obscured_token

    @property
    def obscured_token(self):
        if self.token:
            return "{}***".format(self.token[:4])


class LegacyTokenProxy(Token):
    class Meta:
        proxy = True
        verbose_name = 'Legacy token'
        verbose_name_plural = 'Legacy tokens'

    def __str__(self):
        return self.obscured_token

    def __unicode__(self):
        return self.obscured_token

    @property
    def obscured_token(self):
        if self.key:
            return "{}***".format(self.key[:4])


class ArchiveMixin(cachemodel.CacheModel):

    archived = models.BooleanField(default=False)

    class Meta:
        abstract = True

    @property
    def may_archive(self):
        if not self.assertions:
            return True
        return all([assertion.revoked for assertion in self.assertions])

    @transaction.atomic
    def archive(self, **kwargs):
        """
        Recursive archive function that
            - archives all children
            - only publishes the parent of the initially archived entity
            - removes all associated staff memberships without publishing the associated object (the one that is archived)
        """
        publish_parent = kwargs.pop('publish_parent', True)
        if not self.may_archive:
            raise ProtectedError(
                "{} may only be deleted if there are no awarded Assertions.".format(self.__class__.__name__), self)
        if hasattr(self, 'children'):
            for child in self.children:
                child.archive(publish_parent=False)
        for membership in self.staff_items:
            membership.delete(publish_object=False)
        self.archived = True
        self.save()
        if publish_parent:
            try:
                self.parent.publish()
            except AttributeError:  # no parent
                pass