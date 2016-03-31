# Created by wiggins@concentricsky.com on 3/30/16.
from django.conf.urls import url

from pathway.api import PathwayList

urlpatterns = [

    url(r'^$', PathwayList.as_view(), name='pathway_list'),
    #url(r'^/(?P<pk>[^/]+)$', PathwayDetail.as_view(), name='pathway_detail'),
    # url(r'^/pathways/(?P<issuer_slug>[^/]+)/(?P<pk>[^/]+)/badges$', PathwayBadges.as_view(), name='pathway_bages'),

]
