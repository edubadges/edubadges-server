from django.conf.urls import url
from institution.api import FacultyList, FacultyDetail, InstitutionDetail

urlpatterns = [
    url(r'^faculties$', FacultyList.as_view(), name='api_faculty_list'),
    url(r'^faculties/(?P<slug>[^/]+)$', FacultyDetail.as_view(), name='api_faculty_detail'),
    url(r'^institutions/(?P<slug>[^/]+)$', InstitutionDetail.as_view(), name='api_institution_detail'),
    ]

