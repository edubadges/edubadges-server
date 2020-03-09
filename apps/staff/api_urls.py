from django.conf.urls import url

from staff.api import InstitutionStaffList, FacultyStaffList, IssuerStaffList, BadgeClassStaffList

urlpatterns = [
    url(r'^institution/(?P<slug>[^/]+)/create$', InstitutionStaffList.as_view(), name='faculty_staff_list'),
    url(r'^faculty/(?P<slug>[^/]+)/create$', FacultyStaffList.as_view(), name='faculty_staff_list'),
    url(r'^issuer/(?P<slug>[^/]+)/create$', IssuerStaffList.as_view(), name='issuer_staff_list'),
    url(r'^badgeclass/(?P<slug>[^/]+)/create$', BadgeClassStaffList.as_view(), name='badgeclass_staff_list')
    ]

