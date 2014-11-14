from django.conf.urls import patterns, url
from badgeanalysis.views import *

urlpatterns = patterns('badgeanalysis.views',
    url(r'^/schemes/new$', BadgeSchemeCreate.as_view(), name='badgescheme_create'),
    url(r'^/schemes/(?P<slug>[-\w]+)$',BadgeSchemeDetail.as_view(), name='badgescheme_detail'),
    url(r'^/schemes/(?P<slug>[-\w]+)/delete$',BadgeSchemeDelete.as_view(), name='badgescheme_delete')
)
