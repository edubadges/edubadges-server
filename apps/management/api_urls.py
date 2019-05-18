from django.conf.urls import url

from management.api import GroupList, FacultyStats

urlpatterns = [
    url(r'^groups$', GroupList.as_view(), name='management_group_list'),
    url(r'^faculty-stats/(?P<slug>[^/]+)$', FacultyStats.as_view(), name='management_group_list'),
]
