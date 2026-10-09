from badge_connect.api import BadgeConnectView
from django.urls import path

urlpatterns = [
    path("validate/<str:entity_id>", BadgeConnectView.as_view(), name="api_badge_connect"),
]
