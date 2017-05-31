# encoding: utf-8
from __future__ import unicode_literals

from django.conf.urls import url

from backpack.api import BackpackAssertionList, BackpackAssertionDetail, BackpackCollectionList, \
    BackpackCollectionDetail, BackpackAssertionDetailImage
from badgeuser.api import BadgeUserToken, BadgeUserForgotPassword, BadgeUserEmailConfirm, BadgeUserDetail

urlpatterns = [
    # url(r'^import$', BackpackImportBadge.as_view(), name='v2_api_backpack_upload_badge'),

    url(r'^assertions$', BackpackAssertionList.as_view(), name='v2_api_backpack_assertion_list'),
    url(r'^assertions/(?P<entity_id>[^/]+)$', BackpackAssertionDetail.as_view(), name='v2_api_backpack_assertion_detail'),
    url(r'^assertions/(?P<entity_id>[^/]+)/image$', BackpackAssertionDetailImage.as_view(), name='v2_api_backpack_assertion_detail_image'),

    url(r'^collections$', BackpackCollectionList.as_view(), name='v2_api_backpack_collection_list'),
    url(r'^collections/(?P<entity_id>[^/]+)$', BackpackCollectionDetail.as_view(), name='v2_api_backpack_collection_detail'),

    # url(r'^share/assertion/(?P<entity_id>[^/]+)$', BackpackShareAssertion.as_view(), name='v2_api_share_assertion'),
    # url(r'^share/collection/(?P<entity_id>[^/]+)$', BackpackShareCollection.as_view(), name='v2_api_share_collection'),
]