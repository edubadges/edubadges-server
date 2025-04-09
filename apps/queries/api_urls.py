from django.urls import re_path

from queries.api import DirectAwards, BadgeClasses, CatalogBadgeClasses, CurrentInstitution, Issuers, Faculties, Users, \
    Notifications

urlpatterns = [
    re_path(r'^direct-awards', DirectAwards.as_view(), name='api_queries_da'),
    re_path(r'^badge-classes', BadgeClasses.as_view(), name='api_queries_bc'),
    re_path(r'^issuers', Issuers.as_view(), name='api_queries_iss'),
    re_path(r'^faculties', Faculties.as_view(), name='api_queries_fac'),
    re_path(r'^users', Users.as_view(), name='api_queries_users'),
    re_path(r'^notifications', Notifications.as_view(), name='api_queries_notifications'),
    re_path(r'^current-institution', CurrentInstitution.as_view(), name='api_queries_ins'),
    re_path(r'^catalog/badge-classes', CatalogBadgeClasses.as_view(), name='api_queries_cat'),
]
