from django.conf.urls import url

from .views import health

urlpatterns = [
    url(r'^$', health, name='server_health'),
]
