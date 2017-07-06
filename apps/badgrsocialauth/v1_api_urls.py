from django.conf.urls import url

from badgrsocialauth.api import BadgrSocialAccountList, BadgrSocialAccountDetail

urlpatterns = [
    url(r'^socialaccounts$', BadgrSocialAccountList.as_view(), name='v1_api_user_socialaccount_list'),
    url(r'^socialaccounts/(?P<id>[^/]+)$', BadgrSocialAccountDetail.as_view(), name='v1_api_user_socialaccount_detail')
]
