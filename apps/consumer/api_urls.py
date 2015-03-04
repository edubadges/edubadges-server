from django.conf.urls import patterns, url
from consumer.api import ConsumerBadgesList, ConsumerBadgeDetail

urlpatterns = patterns('consumer.api_views',
   url(r'^/badges$', ConsumerBadgesList.as_view(), name='consumer_badge_list'),
   url(r'^/badges/(?P<pk>[0-9]+)$', ConsumerBadgeDetail.as_view(), name='consumer_badge_detail')
)
