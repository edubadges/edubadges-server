from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns

from .public_api import (IssuerJson, IssuerImage, BadgeClassJson,
                         BadgeClassImage, BadgeClassCriteria, BadgeInstanceJson,
                         BadgeInstanceImage)

json_patterns = [
    url(r'^/issuers/(?P<entity_id>[-\w]+)$', IssuerJson.as_view(), name='issuer_json'),
    url(r'^/badges/(?P<entity_id>[-\w]+)$', BadgeClassJson.as_view(), name='badgeclass_json'),
    url(r'^/assertions/(?P<entity_id>[-\w]+)$', BadgeInstanceJson.as_view(), name='badgeinstance_json'),
]

image_patterns = [
    url(r'^/issuers/(?P<entity_id>[-\w]+)/image$', IssuerImage.as_view(), name='issuer_image'),
    url(r'^/badges/(?P<entity_id>[-\w]+)/image', BadgeClassImage.as_view(), name='badgeclass_image'),
    url(r'^/assertions/(?P<entity_id>[-\w]+)/image', BadgeInstanceImage.as_view(), name='badgeinstance_image'),
    url(r'^/badges/(?P<entity_id>[-\w]+)/criteria', BadgeClassCriteria.as_view(), name='badgeclass_criteria'),
]

urlpatterns = format_suffix_patterns(json_patterns, allowed=['json']) + image_patterns
