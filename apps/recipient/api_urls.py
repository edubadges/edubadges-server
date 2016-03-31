# Created by wiggins@concentricsky.com on 3/31/16.
from django.conf.urls import url

from recipient.api import RecipientGroupList, RecipientGroupDetail, RecipientGroupMembershipList, \
    RecipientGroupMembershipDetail

urlpatterns = [
    url(r'^$', RecipientGroupList.as_view(), name='recipient_group_list'),
    url(r'^/(?P<group_pk>[^/]+)$', RecipientGroupDetail.as_view(), name='recipient_group_detail'),
    url(r'^/(?P<group_pk>[^/]+)/members$', RecipientGroupMembershipList.as_view(), name='recipient_group_membership_list'),
    url(r'^/(?P<group_pk>[^/]+)/members/(?P<membership_pk>[^/]+)$', RecipientGroupMembershipDetail.as_view(), name='recipient_group_membership_detail'),

]