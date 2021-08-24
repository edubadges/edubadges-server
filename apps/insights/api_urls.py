from django.conf.urls import url

from insights.api import InsightsView

urlpatterns = [
    url(r'^insight$', InsightsView.as_view(), name='api_insight'),
]

