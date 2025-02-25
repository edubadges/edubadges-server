from django.urls import path

from badge_connect.api import BadgeConnectView

urlpatterns = [
    path('validate/<str:entity_id>', BadgeConnectView.as_view(), name='api_badge_connect'),
]
