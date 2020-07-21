from django.conf.urls import url
from institution.api import FacultyList, FacultyDetail, InstitutionDetail
from institution.public_api import PublicInstitutionDetail


urlpatterns = [
    url(r'^edit/(?P<entity_id>[^/]+)$', InstitutionDetail.as_view(), name='api_institution_detail'),
    url(r'^faculties/create$', FacultyList.as_view(), name='api_faculty_list'),
    url(r'^faculties/edit/(?P<entity_id>[^/]+)$', FacultyDetail.as_view(), name='api_faculty_detail'),
    #public urls
    url(r'^public/(?P<shac_home>[^/]+)$', PublicInstitutionDetail.as_view(), name='api_public_institution_detail'),
    ]

