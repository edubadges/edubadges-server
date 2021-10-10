from backpack.api import BackpackAssertionList, BackpackAssertionDetail, BackpackAssertionDetailImage, \
    ShareBackpackAssertion, ImportedAssertionList, ImportedAssertionDetail, ImportedAssertionDelete
from django.conf.urls import url

urlpatterns = [

    url(r'^badges$', BackpackAssertionList.as_view(), name='v1_api_localbadgeinstance_list'),
    url(r'^badges/(?P<entity_id>[^/]+)$', BackpackAssertionDetail.as_view(), name='v1_api_localbadgeinstance_detail'),
    url(r'^badges/(?P<entity_id>[^/]+)/image$', BackpackAssertionDetailImage.as_view(), name='v1_api_localbadgeinstance_image'),

    # legacy v1 endpoints
    url(r'^share/badge/(?P<entity_id>[^/]+)$', ShareBackpackAssertion.as_view(), name='v1_api_analytics_share_badge'),

    # imported assertions
    url(r'^imported/assertions$', ImportedAssertionList.as_view(), name='api_imported_assertions_list'),
    url(r'^imported/assertions/detail/(?P<entity_id>[^/]+)$', ImportedAssertionDetail.as_view(), name='api_imported_assertion_detail'),
    url(r'^imported/assertions/edit/(?P<entity_id>[^/]+)$', ImportedAssertionDetail.as_view(), name='api_imported_assertions_edit'),
    url(r'^imported/assertions/delete/(?P<entity_id>[^/]+)$', ImportedAssertionDelete.as_view(), name='api_imported_assertions_delete'),

]

