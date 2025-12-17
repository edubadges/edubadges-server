from django.urls import path

from institution.api import (
    FacultyArchiveView,
    FacultyAuditLog,
    FacultyDetail,
    FacultyDeleteView,
    FacultyList,
    InstitutionAuditLog,
    InstitutionDetail,
    InstitutionsTagUsage,
    PublicCheckInstitutionsValidity,
)

urlpatterns = [
    path('edit/<str:entity_id>', InstitutionDetail.as_view(), name='api_institution_detail'),
    path('auditlog', InstitutionAuditLog.as_view(), name='institution_auditlog'),
    path('faculties/create', FacultyList.as_view(), name='api_faculty_list'),
    path('faculties/edit/<str:entity_id>', FacultyDetail.as_view(), name='api_faculty_detail'),
    path('faculties/delete/<str:entity_id>', FacultyDeleteView.as_view(), name='api_faculty_delete'),
    path('faculties/archive/<str:entity_id>', FacultyArchiveView.as_view(), name='faculty_archive'),
    path('faculties/auditlog', FacultyAuditLog.as_view(), name='faculty_auditlog'),
    # public endpoint
    path('check', PublicCheckInstitutionsValidity.as_view(), name='api_check_institution_validity'),
    path('tags', InstitutionsTagUsage.as_view(), name='api_institutions_tag_usage'),
]
