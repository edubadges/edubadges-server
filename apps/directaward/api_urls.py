from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from directaward.api import (DirectAwardBundleList, DirectAwardDetail, DirectAwardAccept, DirectAwardRevoke,
                             DirectAwardResend, DirectAwardDelete)

urlpatterns = [
    url(r'^create$', csrf_exempt(DirectAwardBundleList.as_view()), name='direct_award_bundle_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', DirectAwardDetail.as_view(), name='direct_award_detail'),
    url(r'^accept/(?P<entity_id>[^/]+)$', DirectAwardAccept.as_view(), name='direct_award_accept'),
    url(r'^revoke-direct-awards$', DirectAwardRevoke.as_view(), name='direct_award_revoke'),
    url(r'^resend-direct-awards$', DirectAwardResend.as_view(), name='direct_award_resend'),
    url(r'^delete-direct-awards$', DirectAwardDelete.as_view(), name='direct_award_delete'),
]
