from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from directaward.api import (
    DirectAwardBundleList,
    DirectAwardAccept,
    DirectAwardRevoke,
    DirectAwardDelete,
    DirectAwardBundleView,
)

urlpatterns = [
    path('create', csrf_exempt(DirectAwardBundleList.as_view()), name='direct_award_bundle_list'),
    path('bundle/<str:entity_id>', DirectAwardBundleView.as_view(), name='direct_award_detail'),
    path('accept/<str:entity_id>', DirectAwardAccept.as_view(), name='direct_award_accept'),
    path('revoke-direct-awards', DirectAwardRevoke.as_view(), name='direct_award_revoke'),
    path('delete-direct-awards', DirectAwardDelete.as_view(), name='direct_award_delete'),
]
