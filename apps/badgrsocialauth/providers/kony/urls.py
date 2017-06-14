from allauth.socialaccount.providers.oauth.urls import default_urlpatterns

from badgrsocialauth.providers.kony.provider import KonyProvider

urlpatterns = default_urlpatterns(KonyProvider)