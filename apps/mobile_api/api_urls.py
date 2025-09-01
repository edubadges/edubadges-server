from django.urls import re_path

from mobile_api.api import BadgeInstances

urlpatterns = [
    re_path(r'^badge-instances', BadgeInstances.as_view(), name='mobile_api_badge_instances'),
]
