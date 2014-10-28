from django.conf.urls import patterns, url
from homepage.views import *

urlpatterns = patterns('homepage.views',
    url(r'^$', HomeIndexView.as_view(), name='home'),
)
