from django.conf.urls import url

from insights.api import InsightsView, InstitutionAdminsView, InstitutionBadgesView, InstitutionMicroCredentials

urlpatterns = [
    url(r'^insight$', InsightsView.as_view(), name='api_insight'),
    url(r'^institution/admins$', InstitutionAdminsView.as_view(), name='api_institution_admins'),
    url(r'^institution/badges$', InstitutionBadgesView.as_view(), name='api_institution_badges'),
    url(r'^institution/micro-credentials$', InstitutionMicroCredentials.as_view(),
        name='api_institution_micro_credentials'),
]
