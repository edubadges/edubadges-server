from django.urls import path

from insights.api import (
    InsightsView,
    InstitutionAdminsView,
    InstitutionBadgesView,
    InstitutionMicroCredentials,
    CountMicroCredentials,
    MicroCredentialsBadgeOverview,
    InstitutionBadgesOverview,
    IssuerMembers, SectorBadgesOverview,
)

urlpatterns = [
    path('insight', InsightsView.as_view(), name='api_insight'),
    path('institution/admins', InstitutionAdminsView.as_view(), name='api_institution_admins'),
    path('institution/badges', InstitutionBadgesView.as_view(), name='api_institution_badges'),
    path(
        'institution/micro-credentials', InstitutionMicroCredentials.as_view(), name='api_institution_micro_credentials'
    ),
    path(
        'institution/micro-credentials-count',
        CountMicroCredentials.as_view(),
        name='api_institution_micro_credentials_count',
    ),
    path(
        'institution/micro-credentials-badges',
        MicroCredentialsBadgeOverview.as_view(),
        name='api_institution_micro_credentials_badges',
    ),
    path('institution/badges-overview', InstitutionBadgesOverview.as_view(), name='api_institution_badges_overview'),
    path('institution/sector-overview', SectorBadgesOverview.as_view(), name='api_sector_badges_overview'),
    path('institution/issuer-members', IssuerMembers.as_view(), name='api_institution_issuer_members'),
]
