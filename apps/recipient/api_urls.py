# Created by wiggins@concentricsky.com on 3/31/16.
from django.conf.urls import url

from recipient.api import RecipientGroupList, RecipientGroupDetail

urlpatterns = [
    url(r'^$', RecipientGroupList.as_view(), name='recipient_group_list'),
    url(r'^/(?P<pk>[^/]+)$', RecipientGroupDetail.as_view(), name='recipient_group_detail'),
    # url(r'^/(?P<pk>[^/]+)/members$', RecipientGroupMembershipList.as_view(), name='recipient_group_detail'),

]