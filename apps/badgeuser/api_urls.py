from django.conf.urls import patterns, url
from badgeuser.api import BadgeUserDetail, BadgeUserList

urlpatterns = patterns('badgeuser.views',
    url(r'^/(?P<username>[-\w]+)$', BadgeUserDetail.as_view(), name='user_detail'),
    url(r'^', BadgeUserList.as_view(), name='user_list'),
)
