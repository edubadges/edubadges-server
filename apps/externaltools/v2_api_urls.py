# encoding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url

from externaltools.api import ExternalToolList


urlpatterns = [
    url(r'^$', ExternalToolList.as_view(), name='externaltools_list'),
]
