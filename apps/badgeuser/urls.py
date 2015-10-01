from django.conf.urls import patterns, url

from .api import BadgeUserDetail
from .views import UpdateBadgeUserIsActive


urlpatterns = patterns('badgeuser.views',
    url(r'^/enabled$', UpdateBadgeUserIsActive.as_view(), name='account_enabled'),
    url(r'^/(?P<username>[^/]+)$', BadgeUserDetail.as_view(), name='user_detail'),
)
