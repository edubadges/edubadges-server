from django.conf import settings
from django.db import models
AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')
from signing import utils

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
            raise ValueError('Password does not match the one belonging to this Symmetric Key')


class PrivateKey(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL)
    symmetric_key = models.ForeignKey('signing.SymmetricKey')
    encrypted_private_key = models.TextField()
    initialization_vector = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    associated_data = models.CharField(max_length=255)
    time_created = models.DateTimeField()
    hash_of_public_key = models.CharField(max_length=255)

    def get_params(self):
        return {'initialization_vector': self.initialization_vector,
                'encrypted_private_key': self.encrypted_private_key,
                'tag': self.tag,
                'associated_data': self.associated_data,
                'hash_of_public_key': self.hash_of_public_key,
                'time_created': self.time_created.strftime('%Y-%m-%dT%H:%M:%SZ')}

