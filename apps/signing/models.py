from django.conf import settings
from django.db import models
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


class PrivateKey(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL)
    symmetric_key = models.ForeignKey('signing.SymmetricKey')
    encrypted_private_key = models.TextField()
    initialization_vector = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    associated_data = models.CharField(max_length=255)
    time_created = models.DateTimeField()
    hash_of_public_key = models.CharField(max_length=255)
