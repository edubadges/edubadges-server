from django.conf.urls import patterns, url
from earner.api import EarnerBadgesList, EarnerBadgeDetail

urlpatterns = patterns('earner.api_views',
   url(r'^/badges$', EarnerBadgesList.as_view(), name='earner_badge_list'),
   url(r'^/badges/(?P<pk>[0-9]+)$', EarnerBadgeDetail.as_view(), name='earner_badge_detail')
)
