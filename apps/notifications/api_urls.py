from django.urls import path

from notifications.api import NotificationsView

urlpatterns = [
    path('notifications', NotificationsView.as_view(), name='api_notifications'),
]
