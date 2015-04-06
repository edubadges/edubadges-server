from django.conf.urls import patterns, url
from badgeuser.api import BadgeUserDetail, BadgeUserList, BadgeUserToken

urlpatterns = patterns('badgeuser.views',
    # url(r'^$', BadgeUserList.as_view(), name='user_list'),
    # url(r'^/users/(?P<username>[-\w]+)$', BadgeUserDetail.as_view(), name='user_detail'),
    url(r'^/auth-token$', BadgeUserToken.as_view(), name='user_auth_token'),
)
