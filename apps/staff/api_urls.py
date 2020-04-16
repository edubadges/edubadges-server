from django.conf.urls import url

from staff.api import InstitutionStaffList, FacultyStaffList, IssuerStaffList, BadgeClassStaffList, \
    InstitutionStaffDetail, FacultyStaffDetail, IssuerStaffDetail, BadgeClassStaffDetail

urlpatterns = [
    url(r'^institution/(?P<entity_id>[^/]+)/create$', InstitutionStaffList.as_view(), name='faculty_staff_list'),
    url(r'^institution/change/(?P<entity_id>[^/]+)$', InstitutionStaffDetail.as_view(), name='faculty_staff_list'),
    url(r'^faculty/(?P<entity_id>[^/]+)/create$', FacultyStaffList.as_view(), name='faculty_staff_list'),
    url(r'^faculty/change/(?P<entity_id>[^/]+)$', FacultyStaffDetail.as_view(), name='faculty_staff_list'),
    url(r'^issuer/(?P<entity_id>[^/]+)/create$', IssuerStaffList.as_view(), name='issuer_staff_list'),
    url(r'^issuer/change/(?P<entity_id>[^/]+)$', IssuerStaffDetail.as_view(), name='faculty_staff_list'),
    url(r'^badgeclass/(?P<entity_id>[^/]+)/create$', BadgeClassStaffList.as_view(), name='badgeclass_staff_list'),
    url(r'^badgeclass/change/(?P<entity_id>[^/]+)$', BadgeClassStaffDetail.as_view(), name='faculty_staff_list'),
    ]

