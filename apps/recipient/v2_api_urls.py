# # encoding: utf-8
#
#
# from django.conf.urls import url
#
# from recipient.api import IssuerRecipientGroupList, RecipientGroupDetail
#
# urlpatterns = [
#     url(r'^issuers/(?P<entity_id>[^/]+)/recipientGroups$', IssuerRecipientGroupList.as_view(), name='v2_api_issuer_recipient_group_list'),
#     url(r'^recipientGroups/(?P<entity_id>[^/]+)$', RecipientGroupDetail.as_view(), name='v2_api_recipient_group_detail'),
#     # url(r'^recipientGroups$', AllRecipientGroupsList.as_view(), name='v2_api_all_recipient_groups_list'),
# ]
#
#
