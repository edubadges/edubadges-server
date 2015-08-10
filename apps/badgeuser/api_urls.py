from django.conf.urls import patterns, url
from badgeuser.api import BadgeUserDetail, BadgeUserToken

urlpatterns = patterns('badgeuser.api_views',
    url(r'^/auth-token$', BadgeUserToken.as_view(), name='user_auth_token'),
    url(r'^/(?P<username>[-.\w]+)$', BadgeUserDetail.as_view(), name='api_user_detail')
)
