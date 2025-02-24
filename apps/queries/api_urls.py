from django.conf.urls import url

from queries.api import DirectAwards, BadgeClasses, CatalogBadgeClasses, CurrentInstitution, Issuers, Faculties, Users

urlpatterns = [
    url(r'^direct-awards', DirectAwards.as_view(), name='api_queries_da'),
    url(r'^badge-classes', BadgeClasses.as_view(), name='api_queries_bc'),
    url(r'^issuers', Issuers.as_view(), name='api_queries_iss'),
    url(r'^faculties', Faculties.as_view(), name='api_queries_fac'),
    url(r'^users', Users.as_view(), name='api_queries_users'),
    url(r'^current-institution', CurrentInstitution.as_view(), name='api_queries_ins'),
    url(r'^catalog/badge-classes', CatalogBadgeClasses.as_view(), name='api_queries_cat'),

]
