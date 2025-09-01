from django.urls import re_path, path

from mobile_api.api import BadgeInstances, BadgeInstanceDetail

urlpatterns = [
    path('badge-instances', BadgeInstances.as_view(), name='mobile_api_badge_instances'),
    path('badge-instance-detail/<str:entity_id>', BadgeInstanceDetail.as_view(), name='mobile_api_badge_instance_detail'),
]
