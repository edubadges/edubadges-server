from django.conf.urls import url
from institution.api import FacultyIssuerList, InstitutionFacultyList, FacultyDetail, InstitutionDetail

urlpatterns = [
    url(r'^faculties/(?P<slug>[^/]+)/issuers$', FacultyIssuerList.as_view(), name='api_faculty_list'),
    url(r'^faculties$', InstitutionFacultyList.as_view(), name='api_faculty_list'),
    url(r'^faculties/(?P<slug>[^/]+)$', FacultyDetail.as_view(), name='api_faculty_detail'),
    url(r'^institutions/(?P<slug>[^/]+)$', InstitutionDetail.as_view(), name='api_institution_detail'),
    ]

