from management.api import GroupList, FacultyStats
from django.conf.urls import url

urlpatterns = [
    url(r'^groups$', GroupList.as_view(), name='management_group_list'),
    url(r'^faculty-stats/(?P<slug>[^/]+)$', FacultyStats.as_view(), name='management_group_list'),
]
