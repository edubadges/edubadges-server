from django.conf.urls import patterns, url
from contact.views import *

urlpatterns = patterns('contact.views',
    url(r'^$', Contact.as_view(), name='contact'),
    url(r'^/thanks$', ContactThanks.as_view(), name='contact_thanks'),
)
