from django.conf.urls import url

from insights.api import InsightsView, InstitutionAdminsView, InstitutionBadgesView

urlpatterns = [
    url(r'^insight$', InsightsView.as_view(), name='api_insight'),
    url(r'^institution/admins$', InstitutionAdminsView.as_view(), name='api_institution_admins'),
    url(r'^institution/badges$', InstitutionBadgesView.as_view(), name='api_institution_admins'),
]
