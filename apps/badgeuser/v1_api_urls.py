from django.conf.urls import url

from badgeuser.api import BadgeUserToken, BadgeUserEmailList, BadgeUserEmailDetail, \
    BadgeUserForgotPassword, \
    BadgeUserEmailConfirm, BadgeUserDetail

urlpatterns = [
    url(r'^auth-token$', BadgeUserToken.as_view(), name='v1_api_user_auth_token'),
    url(r'^profile$', BadgeUserDetail.as_view(), name='v1_api_user_profile'),
    url(r'^forgot-password$', BadgeUserForgotPassword.as_view(), name='v1_api_user_forgot_password'),
    url(r'^emails$', BadgeUserEmailList.as_view(), name='v1_api_user_emails'),
    url(r'^emails/(?P<id>[^/]+)$', BadgeUserEmailDetail.as_view(), name='v1_api_user_email_detail'),
    url(r'^legacyconfirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='legacy_user_email_confirm'),
    url(r'^confirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v1_api_user_email_confirm')
]
