from django.conf.urls import patterns, url
from views import EarnerPortal

urlpatterns = patterns('earner.views',
    url(r'^', EarnerPortal.as_view(), name='earner_portal'),
)
