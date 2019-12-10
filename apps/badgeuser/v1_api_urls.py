from badgeuser.api import BadgeUserToken, BadgeUserForgotPassword, BadgeUserEmailConfirm, BadgeUserDetail, \
    BadgeUserList, BadgeUserManagementDetail
from badgeuser.api_v1 import BadgeUserEmailList, BadgeUserEmailDetail, BadgeUserFacultyList
from django.conf.urls import url

urlpatterns = [
    url(r'^auth-token$', BadgeUserToken.as_view(), name='v1_api_user_auth_token'),
    url(r'^profile$', BadgeUserDetail.as_view(), name='v1_api_user_profile'),
    url(r'^forgot-password$', BadgeUserForgotPassword.as_view(), name='v1_api_auth_forgot_password'),
    url(r'^emails$', BadgeUserEmailList.as_view(), name='v1_api_user_emails'),
    url(r'^faculties$', BadgeUserFacultyList.as_view(), name='v1_api_user_faculties'),
    url(r'^emails/(?P<id>[^/]+)$', BadgeUserEmailDetail.as_view(), name='v1_api_user_email_detail'),
    url(r'^legacyconfirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='legacy_user_email_confirm'),
    url(r'^confirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v1_api_user_email_confirm'),
    url(r'^users$', BadgeUserList.as_view(), name='v1_api_user_list'),
    url(r'^users/(?P<slug>[^/]+)$', BadgeUserManagementDetail.as_view(), name='v1_api_user_management_detail'),
]
