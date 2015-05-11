from django.conf.urls import patterns, url
from badgeuser.api import BadgeUserDetail, BadgeUserToken

urlpatterns = patterns('badgeuser.views',
    url(r'^/(?P<username>[-\w]+)$', BadgeUserDetail.as_view(), name='user_detail')
)
