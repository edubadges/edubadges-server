from django.conf.urls import url
from institution.api import FacultyIssuerList #, FacultyDetail

urlpatterns = [
    url(r'^faculties/(?P<slug>[^/]+)/issuers$', FacultyIssuerList.as_view(), name='api_faculty_list'),
    # url(r'^faculties/(?P<slug>[^/]+)$', FacultyDetail.as_view(), name='api_faculty_detail'),
    ]

