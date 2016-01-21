from django.conf.urls import patterns, url
from badgeuser.api import BadgeUserDetail, BadgeUserToken, BadgeUserProfile

urlpatterns = patterns('badgeuser.api_views',
    url(r'^/auth-token$', BadgeUserToken.as_view(), name='user_auth_token'),
    url(r'^/profile$', BadgeUserProfile.as_view(), name='user_profile'),
    url(r'^/(?P<user_id>[^/]+)$', BadgeUserDetail.as_view(), name='api_user_detail')
)
