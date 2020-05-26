from badgeuser.api import BadgeUserToken, BadgeUserEmailConfirm, BadgeUserDetail, \
    UserCreateProvisionment, AcceptProvisionmentDetail, UserEditProvisionment
from badgeuser.api_v1 import BadgeUserEmailList, BadgeUserEmailDetail
from django.conf.urls import url

urlpatterns = [
    url(r'^auth-token$', BadgeUserToken.as_view(), name='v1_api_user_auth_token'),
    url(r'^profile$', BadgeUserDetail.as_view(), name='v1_api_user_profile'),
    url(r'^emails$', BadgeUserEmailList.as_view(), name='v1_api_user_emails'),
    url(r'^emails/(?P<id>[^/]+)$', BadgeUserEmailDetail.as_view(), name='v1_api_user_email_detail'),
    url(r'^confirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v1_api_user_email_confirm'),
    url(r'^provision/create$', UserCreateProvisionment.as_view(), name='usr_provision_list'),
    url(r'^provision/edit/(?P<entity_id>[^/]+)$', UserEditProvisionment.as_view(), name='usr_provision_list'),
    url(r'^provision/accept/(?P<entity_id>[^/]+)$$', AcceptProvisionmentDetail.as_view(), name='usr_provision_list'),
]
