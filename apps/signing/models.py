import json

from django.conf import settings
from django.db import models
from django.urls import reverse
from entity.models import BaseVersionedEntity
from mainsite.utils import OriginSetting
from signing import timestamping
from signing import utils

AUTH_USER_MODEL = getattr(settings, 'AUTH_USER_MODEL', 'auth.User')


class SymmetricKey(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, default=None)
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
        if self.password_hash != utils.hash_string(password.encode()):
            raise ValueError('Wrong password, please try again.')

    def create_private_key(self, password):
        from signing import tsob
        self.validate_password(password)
        return tsob.create_new_private_key(password, self)


class PrivateKey(models.Model):
    symmetric_key = models.ForeignKey('signing.SymmetricKey', on_delete=models.PROTECT)
    encrypted_private_key = models.TextField()
    initialization_vector = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    associated_data = models.CharField(max_length=255)
    time_created = models.DateTimeField()
    public_key = models.ForeignKey('signing.PublicKey', on_delete=models.PROTECT)

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

    @property
    def private_key(self):
        return PrivateKey.objects.get(public_key=self)


class AssertionTimeStamp(models.Model):
    badge_instance = models.ForeignKey('issuer.BadgeInstance', on_delete=models.CASCADE)
    hash = models.CharField(max_length=64)
    original_json = models.TextField()
    hash_id_nodes = models.TextField(null=True, default=None)
    proof = models.TextField()
    signer = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.PROTECT)

    def proof_is_ready(self):
        return self.proof != ''

    def submit_assertion(self):
        public_key_issuer = self.badge_instance.issuer.create_empty_key_address()
        self.badge_instance.public_key_issuer = public_key_issuer
        self.badge_instance.save()
        assertion_json = self.badge_instance.get_json(expand_badgeclass=True, expand_issuer=True, signed=True,
                                                      public_key_issuer=public_key_issuer)
        canonicalized_json, hashed_json, hash_id_nodes = timestamping.submit_json_for_timestamping(assertion_json)
        self.hash_id_nodes = json.dumps(hash_id_nodes)
        self.hash = hashed_json
        self.original_json = canonicalized_json
        self.save()

    def resubmit_json(self):
        canonicalized_json, hashed_json, hash_id_nodes = timestamping.submit_json_for_timestamping(self.original_json)
        self.hash_id_nodes = json.dumps(hash_id_nodes)
        self.hash = hashed_json
        self.save()

    def _get_hash_id_nodes(self):
        if self.hash_id_nodes:
            return json.loads(self.hash_id_nodes)
        return []

    def get_json_with_proof(self):
        orignal_json = json.loads(self.original_json)
        orignal_json['timestamp'] = json.loads(self.proof)
        return orignal_json

    def update_proof(self):
        at_least_one_is_verified = False
        for id_node in self._get_hash_id_nodes():
            verification = timestamping.verify_proof(id_node)
            print(verification)
            if verification[1] == 'verified':
                at_least_one_is_verified = True
                if 'btc' in verification[2]:  # it has been written to the btc ledger
                    proof_json = timestamping.retrieve_proof(id_node)
                    self.proof = timestamping.canonicalize_json(proof_json)
                    self.save()
                    return
        if not at_least_one_is_verified:
            self.resubmit_json()  # no valid proof data, submit again


class PublicKeyIssuer(BaseVersionedEntity, models.Model):
    """
    Class made for the purpose of creating a temporary address that points to a public key that wil be filled later.
    """
    issuer = models.ForeignKey('issuer.Issuer', on_delete=models.PROTECT)
    public_key = models.ForeignKey('signing.PublicKey', on_delete=models.PROTECT, null=True, default=None)

    def get_absolute_url(self):
        return reverse('signing_public_key_json', kwargs={'entity_id': self.entity_id})

    @property
    def owner_public_url(self):
        return self.issuer.get_url_with_public_key(self)

    @property
    def public_url(self):
        return OriginSetting.HTTP + self.get_absolute_url()

    def get_json(self):
        """Returns the json for in the assertion to be signed"""
        return dict(
            owner=self.owner_public_url,
            type="CryptographicKey",
            id=self.public_url,
            publicKeyPem=self.public_key.public_key_pem
        )
