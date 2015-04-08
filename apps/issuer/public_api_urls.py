from django.conf.urls import patterns, url

from .public_api import (IssuerJson, IssuerImage, BadgeClassJson,
                         BadgeClassImage, BadgeClassCriteria, BadgeInstanceJson,
                         BadgeInstanceImage)


urlpatterns = patterns(
    'issuer.public_api_views',
    url(r'^/issuers/(?P<slug>[\-0-9a-z]+)$', IssuerJson.as_view(), name='issuer_json'),
    url(r'^/issuers/(?P<slug>[\-0-9a-z]+)/image$', IssuerImage.as_view(), name='issuer_image'),

    url(r'^/badges/(?P<slug>[\-0-9a-z]+)$', BadgeClassJson.as_view(), name='badgeclass_json'),
    url(r'^/badges/(?P<slug>[\-0-9a-z]+)/image', BadgeClassImage.as_view(), name='badgeclass_image'),
    url(r'^/badges/(?P<slug>[\-0-9a-z]+)/criteria', BadgeClassCriteria.as_view(), name='badgeclass_criteria'),

    url(r'^/assertions/(?P<slug>[\-0-9a-z]+)$', BadgeInstanceJson.as_view(), name='assertion_json'),
    url(r'^/assertions/(?P<slug>[\-0-9a-z]+)/image', BadgeInstanceImage.as_view(), name='assertion_image'),
)
