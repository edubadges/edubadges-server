from django.conf.urls import url

from management.api import GroupList

urlpatterns = [
    url(r'^groups$', GroupList.as_view(), name='management_group_list'),
]
