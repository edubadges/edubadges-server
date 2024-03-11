from django.conf.urls import url

from insights.api import InsightsView, InstitutionAdminsView, InstitutionBadgesView, InstitutionMicroCredentials, \
    CountMicroCredentials, MicroCredentialsBadgeOverview, InstitutionBadgesOverview, IssuerMembers

urlpatterns = [
    url(r'^insight$', InsightsView.as_view(), name='api_insight'),
    url(r'^institution/admins$', InstitutionAdminsView.as_view(), name='api_institution_admins'),
    url(r'^institution/badges$', InstitutionBadgesView.as_view(), name='api_institution_badges'),
    url(r'^institution/micro-credentials$', InstitutionMicroCredentials.as_view(),
        name='api_institution_micro_credentials'),
    url(r'^institution/micro-credentials-count$', CountMicroCredentials.as_view(),
        name='api_institution_micro_credentials_count'),
    url(r'^institution/micro-credentials-badges$', MicroCredentialsBadgeOverview.as_view(),
        name='api_institution_micro_credentials_badges'),
    url(r'^institution/badges-overview$', InstitutionBadgesOverview.as_view(),
        name='api_institution_badges_overview'),
    url(r'^institution/issuer-members$', IssuerMembers.as_view(),
        name='api_institution_issuer_members'),


]
