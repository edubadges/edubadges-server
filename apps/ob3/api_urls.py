from django.urls import path, re_path

from ob3.api import CredentialsView, OB3CallbackView

urlpatterns = [
    path('v1/ob3/callback', OB3CallbackView.as_view(), name='ob3_callback'),
    re_path(r'^v1/ob3$', CredentialsView.as_view(), name='credentials'),
]
