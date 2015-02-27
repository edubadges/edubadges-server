from django.conf.urls import patterns, url
from django.contrib.auth.decorators import login_required
from issuer.views import *

urlpatterns = patterns('issuer.views',
    url(r'^', EarnerNotificationCreate.as_view(), name='notify_earner')
)
