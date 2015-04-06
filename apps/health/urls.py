from django.conf.urls import patterns, url
from views import health

urlpatterns = patterns('contact.views',
    url(r'^$', health, name='server_health'),
)
