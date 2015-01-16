from django.conf.urls import patterns, url
from issuer.api import EarnerNotificationList, EarnerNotificationDetail

urlpatterns = patterns('issuer.api_views',
   url(r'^/notifications$', EarnerNotificationList.as_view(), name='issuer_notifications_list'),
   url(r'^/notifications/(?P<pk>[0-9]+)$', EarnerNotificationDetail.as_view(), name='issuer_notification_detail')
)
