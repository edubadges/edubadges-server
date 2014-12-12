from django.conf.urls import patterns, url
from earner.views import *

urlpatterns = patterns('earner.views',
   url(r'^/badge$', EarnerBadgeCreate.as_view(), name='earner_badge_create'),
   url(r'^$', EarnerPortal.as_view(), name='main_earner_portal')
)
