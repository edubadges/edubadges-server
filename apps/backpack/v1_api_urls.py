from backpack.api import BackpackAssertionList, BackpackAssertionDetail, BackpackAssertionDetailImage, ShareBackpackAssertion
from django.conf.urls import url

urlpatterns = [

    url(r'^badges$', BackpackAssertionList.as_view(), name='v1_api_localbadgeinstance_list'),
    url(r'^badges/(?P<entity_id>[^/]+)$', BackpackAssertionDetail.as_view(), name='v1_api_localbadgeinstance_detail'),
    url(r'^badges/(?P<entity_id>[^/]+)/image$', BackpackAssertionDetailImage.as_view(), name='v1_api_localbadgeinstance_image'),

    # legacy v1 endpoints
    url(r'^share/badge/(?P<entity_id>[^/]+)$', ShareBackpackAssertion.as_view(), name='v1_api_analytics_share_badge'),
]

