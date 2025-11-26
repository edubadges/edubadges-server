from django.urls import re_path

from ob3.api import CredentialsView

urlpatterns = [
    re_path(r'^v1/ob3', CredentialsView.as_view(), name='credentials'),
]
