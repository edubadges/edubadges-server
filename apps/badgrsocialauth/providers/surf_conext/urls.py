from django.conf.urls import url

from . import views

urlpatterns = [

    # note: in registering the badgr app at SurfConext, the callback url is explicitely registered on 'openid'
    url('^openid/login/callback/$', views.callback, name='surf_conext_callback'),
    url('^openid/login/$', views.login, name="surf_conext_login"),
    url('^openid/login/terms_accepted/(?P<state>[^/]+)/(?P<id_token>[^/]+)', views.after_terms_agreement, name="surf_conext_terms_accepted_callback")
]
