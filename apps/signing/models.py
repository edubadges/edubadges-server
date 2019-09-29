from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models

from entity.models import BaseVersionedEntity
from mainsite.utils import OriginSetting
from signing import utils

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class SymmetricKey(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL)
    password_hash = models.CharField(max_length=255)
    salt = models.CharField(max_length=255)
    length = models.IntegerField()
    n = models.IntegerField()
    r = models.IntegerField()
    p = models.IntegerField()
    current = models.BooleanField()

    class Meta:
        permissions = (('may_sign_assertions', 'User may sign assertions'),)

    def get_params(self):
        return {'salt': self.salt, 'length': self.length, 'n': self.n, 'r': self.r, 'p': self.p}

    def validate_password(self, password):
        if self.password_hash != utils.hash_string(password):
            raise ValueError('Wrong password, please try again.')


class PrivateKey(models.Model):
    symmetric_key = models.ForeignKey('signing.SymmetricKey')
    encrypted_private_key = models.TextField()
    initialization_vector = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    associated_data = models.CharField(max_length=255)
    time_created = models.DateTimeField()
    public_key = models.ForeignKey('signing.PublicKey')

    def get_params(self):
        return {'initialization_vector': self.initialization_vector,
                'encrypted_private_key': self.encrypted_private_key,
                'tag': self.tag,
                'associated_data': self.associated_data,
                'time_created': self.time_created.strftime('%Y-%m-%dT%H:%M:%SZ'),
                'public_key': self.public_key.public_key_pem
                }

    @property
    def user(self):
        return self.symmetric_key.user


class PublicKey(BaseVersionedEntity, models.Model):
    public_key_pem = models.TextField()
    time_created = models.DateTimeField()
    issuer = models.ForeignKey('issuer.Issuer')

    def get_absolute_url(self):
        return reverse('signing_public_key_json', kwargs={'entity_id': self.entity_id})

    @property
    def public_url(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    @property
    def private_key(self):
        return PrivateKey.objects.get(public_key=self)

    def get_json(self):
        """Returns the json for in the signed assertion"""
        return dict(
            owner=self.issuer.public_url,
            type="CryptographicKey",
            id=self.public_url,
            publicKeyPem=self.public_key_pem
        )
