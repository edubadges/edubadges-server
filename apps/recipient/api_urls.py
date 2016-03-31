# Created by wiggins@concentricsky.com on 3/31/16.
from django.conf.urls import url

from recipient.api import RecipientGroupList, RecipientGroupDetail, RecipientGroupMembershipList, \
    RecipientGroupMembershipDetail

urlpatterns = [
    url(r'^$', RecipientGroupList.as_view(), name='recipient_group_list'),
    url(r'^/(?P<group_slug>[^/]+)$', RecipientGroupDetail.as_view(), name='recipient_group_detail'),
    url(r'^/(?P<group_slug>[^/]+)/members$', RecipientGroupMembershipList.as_view(), name='recipient_group_membership_list'),
    url(r'^/(?P<group_slug>[^/]+)/members/(?P<membership_slug>[^/]+)$', RecipientGroupMembershipDetail.as_view(), name='recipient_group_membership_detail'),

]