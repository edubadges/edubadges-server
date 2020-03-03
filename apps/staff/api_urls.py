from django.conf.urls import url

from staff.api import FacultyStaffList, IssuerStaffList, BadgeClassStaffList

urlpatterns = [
    url(r'^faculty/(?P<slug>[^/]+)', FacultyStaffList.as_view(), name='faculty_staff_list'),
    url(r'^issuer/(?P<slug>[^/]+)$', IssuerStaffList.as_view(), name='issuer_staff_list'),
    url(r'^badgeclass/(?P<slug>[^/]+)$', BadgeClassStaffList.as_view(), name='badgeclass_staff_list')
    ]

