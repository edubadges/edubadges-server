from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .public_api import (IssuerJson, IssuerImage, BadgeClassJson,
                         BadgeClassImage, BadgeClassCriteria, BadgeInstanceJson,
                         BadgeInstanceImage)

json_patterns = [
    url(r'^/issuers/(?P<entity_id>[^/]+)$', IssuerJson.as_view(), name='issuer_json'),
    url(r'^/badges/(?P<entity_id>[^/]+)$', BadgeClassJson.as_view(), name='badgeclass_json'),
    url(r'^/assertions/(?P<entity_id>[^/]+)$', BadgeInstanceJson.as_view(), name='badgeinstance_json'),
]

image_patterns = [
    url(r'^/issuers/(?P<entity_id>[^/]+)/image$', IssuerImage.as_view(), name='issuer_image'),
    url(r'^/badges/(?P<entity_id>[^/]+)/image', BadgeClassImage.as_view(), name='badgeclass_image'),
    url(r'^/assertions/(?P<entity_id>[^/]+)/image', BadgeInstanceImage.as_view(), name='badgeinstance_image'),
    url(r'^/badges/(?P<entity_id>[^/]+)/criteria', BadgeClassCriteria.as_view(), name='badgeclass_criteria'),
]

urlpatterns = format_suffix_patterns(json_patterns, allowed=['json']) + image_patterns
