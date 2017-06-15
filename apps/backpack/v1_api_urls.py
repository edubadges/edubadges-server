from django.conf.urls import url

from backpack.api import BackpackAssertionList, BackpackAssertionDetail, BackpackAssertionDetailImage, \
    BackpackCollectionList, BackpackCollectionDetail, ShareBackpackAssertion, ShareBackpackCollection
from backpack.api_v1 import CollectionLocalBadgeInstanceList, CollectionLocalBadgeInstanceDetail, \
    CollectionGenerateShare

urlpatterns = [

    url(r'^badges$', BackpackAssertionList.as_view(), name='v1_api_localbadgeinstance_list'),
    url(r'^badges/(?P<slug>[^/]+)$', BackpackAssertionDetail.as_view(), name='v1_api_localbadgeinstance_detail'),
    url(r'^badges/(?P<slug>[^/]+)/image$', BackpackAssertionDetailImage.as_view(), name='v1_api_localbadgeinstance_image'),

    url(r'^collections$', BackpackCollectionList.as_view(), name='v1_api_collection_list'),
    url(r'^collections/(?P<slug>[-\w]+)$', BackpackCollectionDetail.as_view(), name='v1_api_collection_detail'),

    # legacy v1 endpoints
    url(r'^collections/(?P<slug>[-\w]+)/badges$', CollectionLocalBadgeInstanceList.as_view(), name='v1_api_collection_badges'),
    url(r'^collections/(?P<collection_slug>[-\w]+)/badges/(?P<slug>[^/]+)$', CollectionLocalBadgeInstanceDetail.as_view(), name='v1_api_collection_localbadgeinstance_detail'),
    url(r'^collections/(?P<slug>[-\w]+)/share$', CollectionGenerateShare.as_view(), name='v1_api_collection_generate_share'),

    url(r'^share/badge/(?P<slug>[^/]+)$', ShareBackpackAssertion.as_view(), name='v1_api_analytics_share_badge'),
    url(r'^share/collection/(?P<slug>[^/]+)$', ShareBackpackCollection.as_view(), name='v1_api_analytics_share_collection'),
]
