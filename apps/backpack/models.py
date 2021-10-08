# encoding: utf-8


from urllib.parse import urljoin

import cachemodel
import requests
from basic_models.models import CreatedUpdatedAt
from django.conf import settings
from django.db import models

from backpack.sharing import SharingManager
from entity.models import BaseVersionedEntity
from mainsite.models import BaseAuditedModel


class BaseSharedModel(cachemodel.CacheModel, CreatedUpdatedAt):
    SHARE_PROVIDERS = [(p.provider_code, p.provider_name) for code, p in list(SharingManager.ManagerProviders.items())]
    provider = models.CharField(max_length=254, choices=SHARE_PROVIDERS)
    source = models.CharField(max_length=254, default="unknown")

    class Meta:
        abstract = True

    def get_share_url(self, provider, **kwargs):
        raise NotImplementedError()


class BackpackBadgeShare(BaseSharedModel):
    badgeinstance = models.ForeignKey("issuer.BadgeInstance", on_delete=models.CASCADE, null=True)

    def get_share_url(self, provider, **kwargs):
        return SharingManager.share_url(provider, self.badgeinstance, **kwargs)


class ImportedAssertion(BaseAuditedModel, BaseVersionedEntity, models.Model):
    user = models.ForeignKey('badgeuser.BadgeUser', blank=False, null=False, on_delete=models.CASCADE)
    import_url = models.URLField(max_length=512, null=False, blank=False)
    verified = models.BooleanField(default=False)
    code = models.TextField(null=True, blank=True)

    def validate(self, profile_type, recipient_identifier):
        assertion_json = requests.get(self.import_url).json()
        data = {'profile': {profile_type: recipient_identifier}, 'data': assertion_json}
        response = requests.post(json=data,
                                 url=urljoin(settings.VALIDATOR_URL, 'results'),
                                 headers={'Accept': 'application/json'})
        return response.json()
