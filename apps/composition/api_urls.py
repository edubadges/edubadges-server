from django.conf.urls import url

from .api import (LocalBadgeInstanceList, LocalBadgeInstanceDetail,
                  CollectionList, CollectionDetail, CollectionGenerateShare,
                  CollectionLocalBadgeInstanceList,
                  CollectionLocalBadgeInstanceDetail, LocalBadgeInstanceImage, ShareBadge,
                  ShareCollection)

urlpatterns = [

    url(r'^/badges$', LocalBadgeInstanceList.as_view(), name='localbadgeinstance_list'),
    url(r'^/badges/(?P<badge_id>[^/]+)$', LocalBadgeInstanceDetail.as_view(), name='localbadgeinstance_detail'),
    url(r'^/badges/(?P<slug>[^/]+)/image$', LocalBadgeInstanceImage.as_view(), name='localbadgeinstance_image'),
    url(r'^/collections$', CollectionList.as_view(), name='collection_list'),
    url(r'^/collections/(?P<slug>[-\w]+)$', CollectionDetail.as_view(), name='collection_detail'),
    url(r'^/collections/(?P<slug>[-\w]+)/badges$', CollectionLocalBadgeInstanceList.as_view(), name='collection_badges'),
    url(r'^/collections/(?P<collection_slug>[-\w]+)/badges/(?P<badge_id>[^/]+)$', CollectionLocalBadgeInstanceDetail.as_view(), name='collection_localbadgeinstance_detail'),
    url(r'^/collections/(?P<slug>[-\w]+)/share$', CollectionGenerateShare.as_view(), name='collection_generate_share'),


    url(r'^/share/badge/(?P<badge_id>[^/]+)$', ShareBadge.as_view(), name='analytics_share_badge'),
    url(r'^/share/collection/(?P<collection_slug>[^/]+)$', ShareCollection.as_view(), name='analytics_share_collection'),
]
