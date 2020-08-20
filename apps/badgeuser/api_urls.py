from badgeuser.api import BadgeUserToken, BadgeUserEmailConfirm, BadgeUserDetail, \
    UserCreateProvisionment, AcceptProvisionmentDetail, UserProvisionmentDetail, \
    AcceptTermsView, PublicTermsView
from badgeuser.api_v1 import BadgeUserEmailList, BadgeUserEmailDetail
from django.conf.urls import url

urlpatterns = [
    url(r'^auth-token$', BadgeUserToken.as_view(), name='v1_api_user_auth_token'),
    url(r'^profile$', BadgeUserDetail.as_view(), name='v1_api_user_profile'),
    url(r'^emails$', BadgeUserEmailList.as_view(), name='v1_api_user_emails'),
    url(r'^emails/(?P<id>[^/]+)$', BadgeUserEmailDetail.as_view(), name='v1_api_user_email_detail'),
    url(r'^confirmemail/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v1_api_user_email_confirm'),
    url(r'^provision/create$', UserCreateProvisionment.as_view(), name='user_provision_list'),
    url(r'^provision/edit/(?P<entity_id>[^/]+)$', UserProvisionmentDetail.as_view(), name='user_provision_detail'),
    url(r'^provision/accept/(?P<entity_id>[^/]+)$$', AcceptProvisionmentDetail.as_view(), name='user_provision_accept'),
    url(r'^terms/accept$', AcceptTermsView.as_view(), name='user_terms_accept'),
    # public endpoints
    url(r'^terms/(?P<user_type>[^/]+)$', PublicTermsView.as_view(), name='public_terms_view'),

]
