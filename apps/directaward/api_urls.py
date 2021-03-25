from django.conf.urls import url

from directaward.api import (DirectAwardList, DirectAwardDetail, DirectAwardAccept)

urlpatterns = [
    url(r'^create$', DirectAwardList.as_view(), name='direct_award_list'),
    url(r'^edit/(?P<entity_id>[^/]+)$', DirectAwardDetail.as_view(), name='direct_award_detail'),
    url(r'^accept/(?P<entity_id>[^/]+)$', DirectAwardAccept.as_view(), name='direct_award_accept')
    ]
