# encoding: utf-8


import cachemodel
from backpack.sharing import SharingManager
from basic_models.models import CreatedUpdatedAt
from django.db import models


class BaseSharedModel(cachemodel.CacheModel, CreatedUpdatedAt):
    SHARE_PROVIDERS = [(p.provider_code, p.provider_name) for code,p in list(SharingManager.ManagerProviders.items())]
    provider = models.CharField(max_length=254, choices=SHARE_PROVIDERS)
    source = models.CharField(max_length=254, default="unknown")

    class Meta:
        abstract = True

    def get_share_url(self, provider, **kwargs):
        raise NotImplementedError()


class BackpackBadgeShare(BaseSharedModel):
    badgeinstance = models.ForeignKey("issuer.BadgeInstance",  on_delete=models.CASCADE, null=True)

    def get_share_url(self, provider, **kwargs):
        return SharingManager.share_url(provider, self.badgeinstance, **kwargs)
