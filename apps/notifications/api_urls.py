from django.conf.urls import url

from notifications.api import NotificationsView

urlpatterns = [
    url(r'^notifications$', NotificationsView.as_view(), name='api_notifications'),
]

