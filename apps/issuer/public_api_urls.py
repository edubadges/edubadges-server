from django.conf.urls import patterns, url

from .public_api import (IssuerJson, IssuerImage, BadgeClassJson,
                         BadgeClassImage, BadgeClassCriteria, BadgeInstanceJson,
                         BadgeInstanceImage)


urlpatterns = patterns(
    'issuer.public_api_views',
    # TODO: Handle url(r'^$),
    url(r'^/issuers/(?P<slug>[-\w]+)$', IssuerJson.as_view(), name='issuer_json'),
    url(r'^/issuers/(?P<slug>[-\w]+)/image$', IssuerImage.as_view(), name='issuer_image'),

    url(r'^/badges/(?P<slug>[-\w]+)$', BadgeClassJson.as_view(), name='badgeclass_json'),
    url(r'^/badges/(?P<slug>[-\w]+)/image', BadgeClassImage.as_view(), name='badgeclass_image'),
    url(r'^/badges/(?P<slug>[-\w]+)/criteria', BadgeClassCriteria.as_view(), name='badgeclass_criteria'),

    url(r'^/assertions/(?P<slug>[-\w]+)$', BadgeInstanceJson.as_view(), name='badgeinstance_json'),
    url(r'^/assertions/(?P<slug>[-\w]+)/image', BadgeInstanceImage.as_view(), name='badgeinstance_image'),
)
