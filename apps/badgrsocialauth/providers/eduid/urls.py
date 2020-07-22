from django.conf.urls import url

from . import views

urlpatterns = [

    # note: in registering the badgr app at SurfConext, the callback url is explicitly registered
    url('^eduid/login/callback/$', views.callback, name='edu_id_callback'),
    url('^eduid/login/$', views.login, name="edu_id_login"),
    url('^eduid/login/terms_accepted/(?P<state>[^/]+)/(?P<id_token>[^/]+)', views.after_terms_agreement,
        name="eduid_terms_accepted_callback")
]
