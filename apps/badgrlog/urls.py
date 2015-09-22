from django.conf.urls import patterns, url

from .views import BadgrLogContextView

urlpatterns = patterns('badgrlog.views',
    url(r'^v1$', BadgrLogContextView.as_view(), name='badgr_log_context'),
)
