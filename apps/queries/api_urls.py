from django.conf.urls import url

from queries.api import DirectAwards

urlpatterns = [
    url(r'^direct-awards', DirectAwards.as_view(), name='api_queries_da'),

]
