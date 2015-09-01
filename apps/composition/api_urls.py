from django.conf.urls import patterns, url

from .api import LocalBadgeInstanceList

urlpatterns = patterns(
    'issuer.api_views',
    url(r'^/badges$', LocalBadgeInstanceList.as_view(), name='local_badgeinstance_list'),
)
