from django.urls import path

from institution.api import (
    FacultyList,
    FacultyDetail,
    FacultyDeleteView,
    InstitutionDetail,
    PublicCheckInstitutionsValidity,
    InstitutionsTagUsage,
)

urlpatterns = [
    path('edit/<str:entity_id>', InstitutionDetail.as_view(), name='api_institution_detail'),
    path('faculties/create', FacultyList.as_view(), name='api_faculty_list'),
    path('faculties/edit/<str:entity_id>', FacultyDetail.as_view(), name='api_faculty_detail'),
    path('faculties/delete/<str:entity_id>', FacultyDeleteView.as_view(), name='api_faculty_delete'),
    # public endpoint
    path('check', PublicCheckInstitutionsValidity.as_view(), name='api_check_institution_validity'),
    path('tags', InstitutionsTagUsage.as_view(), name='api_institutions_tag_usage'),
]
