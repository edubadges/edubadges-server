from django.conf.urls import url

from directaward.api import (DirectAwardBundleList, DirectAwardDetail, DirectAwardAccept, DirectAwardRevoke)

urlpatterns = [
    url(r'^create$', DirectAwardBundleList.as_view(), name='direct_award_bundle_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', DirectAwardDetail.as_view(), name='direct_award_detail'),
    url(r'^accept/(?P<entity_id>[^/]+)$', DirectAwardAccept.as_view(), name='direct_award_accept'),
    url(r'^revoke-direct-awards$', DirectAwardRevoke.as_view(), name='direct_award_revoke'),
]
