from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt

from .views import login, launch, get_jwks, get_lti_context

urlpatterns = [
    url(r'^login/$', csrf_exempt(login), name='lti-login'),
    url(r'^launch/$', csrf_exempt(launch), name='lti-launch'),
    url(r'^jwks/$', get_jwks, name='lti-jwks'),
    url(r'^context/(?P<launch_id>[\w-]+)/$', csrf_exempt(get_lti_context), name='lti-context'),
    # url(r'^api/score/(?P<launch_id>[\w-]+)/(?P<earned_score>[\w-]+)/(?P<time_spent>[\w-]+)/$', score,
    #     name='lti-api-score'),
    # url(r'^api/scoreboard/(?P<launch_id>[\w-]+)/$', scoreboard, name='game-api-scoreboard'),
]
