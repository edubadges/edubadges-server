# encoding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url

from badgeuser.api import BadgeUserToken, BadgeUserForgotPassword, BadgeUserEmailConfirm, BadgeUserDetail, \
    AccessTokenList, AccessTokenDetail, AuthCodeExchange

urlpatterns = [

    url(r'^auth/token$', BadgeUserToken.as_view(), name='v2_api_auth_token'),
    url(r'^auth/forgot-password$', BadgeUserForgotPassword.as_view(), name='v2_api_auth_forgot_password'),
    url(r'^auth/confirm-email/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v2_api_auth_confirm_email'),

    url(r'^auth/tokens$', AccessTokenList.as_view(), name='v2_api_access_token_list'),
    url(r'^auth/tokens/(?P<entity_id>[^/]+)$', AccessTokenDetail.as_view(), name='v2_api_access_token_detail'),


    url(r'^auth/code$', AuthCodeExchange.as_view(), name='v2_api_auth_code_exchange'),

    url(r'^users/(?P<entity_id>self)$', BadgeUserDetail.as_view(), name='v2_api_user_self'),
    url(r'^users/(?P<entity_id>[^/]+)$', BadgeUserDetail.as_view(), name='v2_api_user_detail'),
]