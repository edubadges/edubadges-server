from django.urls import path

from .views import health, readiness, liveness

urlpatterns = [
    path('', health, name='server_health'),
    path('ready', readiness, name='server_readiness'),
    path('live', liveness, name='server_liveness'),
]
