from django.conf.urls import patterns, url
from consumer.views import *

urlpatterns = patterns('consumer.views',
   url(r'^', ConsumerPortal.as_view(), name='main_consumer_portal'),
)
