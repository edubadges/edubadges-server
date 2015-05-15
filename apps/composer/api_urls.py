from django.conf.urls import patterns, url

from .api import *

urlpatterns = patterns(
    'issuer.api_views',
    url(r'^/badges$', EarnerBadgeList.as_view(), name='earner_badge_list'),
    url(r'^/collections$', EarnerCollectionList.as_view(), name='earner_collection_list'),
    url(r'^/collections/(?P<slug>[-\w]+)$', EarnerCollectionDetail.as_view(), name='earner_collection_detail'),
    url(r'^/collections/(?P<slug>[-\w]+)/badges$', EarnerCollectionBadgesList.as_view(), name='earner_collection_badges'),

)
