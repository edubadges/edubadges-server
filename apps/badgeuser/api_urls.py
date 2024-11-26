from django.urls import path, re_path

from badgeuser.api import (
    BadgeUserDetail,
    UserCreateProvisionment,
    AcceptProvisionmentDetail,
    UserProvisionmentDetail,
    AcceptTermsView,
    PublicTermsView,
    UserDeleteView,
)
from badgeuser.api_v1 import BadgeUserEmailList, BadgeUserEmailDetail, FeedbackView

urlpatterns = [
    path("profile", BadgeUserDetail.as_view(), name="v1_api_user_profile"),
    path("feedback", FeedbackView.as_view(), name="v1_api_user_feedback"),
    path("emails", BadgeUserEmailList.as_view(), name="v1_api_user_emails"),
    path("emails/<str:id>", BadgeUserEmailDetail.as_view(), name="v1_api_user_email_detail"),
    path("provision/create", UserCreateProvisionment.as_view(), name="user_provision_list"),
    path("provision/edit/<str:entity_id>", UserProvisionmentDetail.as_view(), name="user_provision_detail"),
    re_path(
        r"^provision/accept/(?P<entity_id>[^/]+)$$", AcceptProvisionmentDetail.as_view(), name="user_provision_accept"
    ),
    path("terms/accept", AcceptTermsView.as_view(), name="user_terms_accept"),
    path("delete/<str:entity_id>", UserDeleteView.as_view(), name="user_delete"),
    # public endpoints
    path("terms/<str:user_type>", PublicTermsView.as_view(), name="public_terms_view"),
]
