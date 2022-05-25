from django.conf.urls import url

from endorsement.api import EndorsementList, EndorsementDetail

urlpatterns = [
    url(r'^create$', EndorsementList.as_view(), name='endorsement_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', EndorsementDetail.as_view(), name='endorsement_edit'),
    url(r'^delete/(?P<entity_id>[^/]+)$', EndorsementDetail.as_view(), name='endorsement_delete'),
]
