from django.urls import path

from staff.api import (
    InstitutionStaffList,
    FacultyStaffList,
    IssuerStaffList,
    BadgeClassStaffList,
    InstitutionStaffDetail,
    FacultyStaffDetail,
    IssuerStaffDetail,
    BadgeClassStaffDetail,
)

urlpatterns = [
    path('institution/<str:entity_id>/create', InstitutionStaffList.as_view(), name='faculty_staff_list'),
    path('institution/change/<str:entity_id>', InstitutionStaffDetail.as_view(), name='faculty_staff_list'),
    path('faculty/<str:entity_id>/create', FacultyStaffList.as_view(), name='faculty_staff_list'),
    path('faculty/change/<str:entity_id>', FacultyStaffDetail.as_view(), name='faculty_staff_list'),
    path('issuer/<str:entity_id>/create', IssuerStaffList.as_view(), name='issuer_staff_list'),
    path('issuer/change/<str:entity_id>', IssuerStaffDetail.as_view(), name='faculty_staff_list'),
    path('badgeclass/<str:entity_id>/create', BadgeClassStaffList.as_view(), name='badgeclass_staff_list'),
    path('badgeclass/change/<str:entity_id>', BadgeClassStaffDetail.as_view(), name='faculty_staff_list'),
]
