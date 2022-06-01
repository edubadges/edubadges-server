from django.conf.urls import url

from endorsement.api import EndorsementList, EndorsementDetail, EndorsementResend

urlpatterns = [
    url(r'^create$', EndorsementList.as_view(), name='endorsement_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', EndorsementDetail.as_view(), name='endorsement_edit'),
    url(r'^delete/(?P<entity_id>[^/]+)$', EndorsementDetail.as_view(), name='endorsement_delete'),
    url(r'^resend/(?P<entity_id>[^/]+)$', EndorsementResend.as_view(), name='endorsement_resend'),
]
