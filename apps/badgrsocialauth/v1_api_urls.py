from django.urls import path

from badgrsocialauth.api import BadgrSocialAccountList, BadgrSocialAccountDetail, BadgrSocialAccountConnect

urlpatterns = [
    path('socialaccounts', BadgrSocialAccountList.as_view(), name='v1_api_user_socialaccount_list'),
    path('socialaccounts/logout', BadgrSocialAccountConnect.as_view(), name='v1_api_user_socialaccount_logout'),
    path('socialaccounts/connect', BadgrSocialAccountConnect.as_view(), name='v1_api_user_socialaccount_connect'),
    path('socialaccounts/<str:id>', BadgrSocialAccountDetail.as_view(), name='v1_api_user_socialaccount_detail'),
]
