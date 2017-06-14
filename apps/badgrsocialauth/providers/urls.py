from allauth.socialaccount.providers.oauth.urls import default_urlpatterns

from badgeuser.providers.kony import KonyProvider

urlpatterns = default_urlpatterns(KonyProvider)