from django.conf.urls import url

from insights.api import InsightsView, InstitutionAdminsView

urlpatterns = [
    url(r'^insight$', InsightsView.as_view(), name='api_insight'),
    url(r'^institution/admins$', InstitutionAdminsView.as_view(), name='api_institution_admins'),
]
