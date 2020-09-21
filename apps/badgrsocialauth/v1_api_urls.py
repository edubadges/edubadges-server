from badgrsocialauth.api import BadgrSocialAccountList, BadgrSocialAccountDetail, BadgrSocialAccountConnect
from django.conf.urls import url

urlpatterns = [
    url(r'^socialaccounts$', BadgrSocialAccountList.as_view(), name='v1_api_user_socialaccount_list'),
    url(r'^socialaccounts/logout$', BadgrSocialAccountConnect.as_view(), name='v1_api_user_socialaccount_logout'),
    url(r'^socialaccounts/connect$', BadgrSocialAccountConnect.as_view(), name='v1_api_user_socialaccount_connect'),
    url(r'^socialaccounts/(?P<id>[^/]+)$', BadgrSocialAccountDetail.as_view(), name='v1_api_user_socialaccount_detail')
]
