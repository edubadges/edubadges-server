from django.conf.urls import *
from search.views import *

urlpatterns = patterns('search.views',
    url(r'^$', SearchResults.as_view(), name='search'),
)
