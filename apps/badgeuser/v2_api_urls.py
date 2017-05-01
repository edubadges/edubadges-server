# encoding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url

from badgeuser.api import BadgeUserToken, BadgeUserForgotPassword, BadgeUserEmailConfirm, BadgeUserProfile

urlpatterns = [

    url(r'^auth/token$', BadgeUserToken.as_view(), name='v2_api_auth_token'),
    # url(r'^auth/signup$', BadgeUserSignup.as_view(), name='v2_api_auth_signup'),
    url(r'^auth/forgot-password$', BadgeUserForgotPassword.as_view(), name='v2_api_auth_forgot_password'),
    url(r'^auth/confirm-email/(?P<confirm_id>[^/]+)$', BadgeUserEmailConfirm.as_view(), name='v2_api_auth_confirm_email'),

    url(r'^users/self$', BadgeUserProfile.as_view(), name='v2_api_user_self'),
]