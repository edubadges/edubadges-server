from django.conf.urls import url

from .views import BadgrLogContextView

urlpatterns = [
    url(r'^v1$', BadgrLogContextView.as_view(), name='badgr_log_context'),
]
