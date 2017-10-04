import StringIO
import abc
import base64
import os
import urlparse

import basic_models
from datetime import datetime, timedelta
from hashlib import sha1, md5
import hmac
import uuid

import requests
from basic_models.managers import ActiveObjectsManager
from basic_models.models import CreatedUpdatedBy, CreatedUpdatedAt, IsActive
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import reverse
from django.db import models

from autoslug import AutoSlugField
import cachemodel
from django.db.models import Manager
from jsonfield import JSONField

from mainsite.utils import OriginSetting, fetch_remote_file_to_storage
from .mixins import ResizeUploadedImage


AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


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

        email_encoded = base64.b64encode(email)
        hashed = hmac.new(secret_key, email_encoded + str(timestamp), sha1)

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
    def get_current(self, request=None):
        if request and request.META.get('HTTP_ORIGIN'):
            origin = request.META.get('HTTP_ORIGIN')
            url = urlparse.urlparse(origin)
            try:
                return self.get(cors=url.netloc)
            except self.model.DoesNotExist:
                pass
        badgr_app_id = getattr(settings, 'BADGR_APP_ID', None)
        if not badgr_app_id:
            raise ImproperlyConfigured("Must specify a BADGR_APP_ID")
        return self.get(id=badgr_app_id)


class BadgrApp(CreatedUpdatedBy, CreatedUpdatedAt, IsActive):
    name = models.CharField(max_length=254)
    cors = models.CharField(max_length=254, unique=True)
    email_confirmation_redirect = models.URLField()
    signup_redirect = models.URLField()
    forgot_password_redirect = models.URLField()
    ui_login_redirect = models.URLField(null=True)
    ui_signup_success_redirect = models.URLField(null=True)
    ui_connect_success_redirect = models.URLField(null=True)
    objects = BadgrAppManager()

    def __unicode__(self):
        return self.cors


class ApplicationInfo(cachemodel.CacheModel):
    application = models.OneToOneField('oauth2_provider.Application')
    icon = models.ImageField(blank=True, null=True)
    name = models.CharField(max_length=254, blank=True, null=True)

    def get_visible_name(self):
        if self.name:
            return self.name
        return self.application.name
