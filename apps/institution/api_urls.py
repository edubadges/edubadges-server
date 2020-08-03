from django.conf.urls import url
from institution.api import FacultyList, FacultyDetail, InstitutionDetail, PublicCheckInstitutionsValidity


urlpatterns = [
    url(r'^edit/(?P<entity_id>[^/]+)$', InstitutionDetail.as_view(), name='api_institution_detail'),
    url(r'^faculties/create$', FacultyList.as_view(), name='api_faculty_list'),
    url(r'^faculties/edit/(?P<entity_id>[^/]+)$', FacultyDetail.as_view(), name='api_faculty_detail'),
    # public endpoint
    url(r'^check$', PublicCheckInstitutionsValidity.as_view(), name='api_check_institution_validity'),
    ]

