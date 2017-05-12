# Created by wiggins@concentricsky.com on 3/31/16.
from django.conf.urls import url

from recipient.api import IssuerRecipientGroupList, RecipientGroupDetail
from recipient.api_v1 import RecipientGroupMembershipList, RecipientGroupMembershipDetail

urlpatterns = [
    # views shared with v2
    url(r'^issuers/(?P<slug>[^/]+)/recipient-groups$', IssuerRecipientGroupList.as_view(), name='v1_api_recipient_group_list'),
    url(r'^issuers/(?P<issuer_slug>[^/]+)/recipient-groups/(?P<slug>[^/]+)$', RecipientGroupDetail.as_view(), name='v1_api_recipient_group_detail'),

    # views only on v1
    url(r'^issuers/(?P<issuer_slug>[^/]+)/recipient-groups/(?P<group_slug>[^/]+)/members$', RecipientGroupMembershipList.as_view(), name='v1_api_recipient_group_membership_list'),
    url(r'^issuers/(?P<issuer_slug>[^/]+)/recipient-groups/(?P<group_slug>[^/]+)/members/(?P<membership_slug>[^/]+)$', RecipientGroupMembershipDetail.as_view(), name='v1_api_recipient_group_membership_detail'),

]