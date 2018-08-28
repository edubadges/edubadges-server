from django.conf.urls import url

from . import views

urlpatterns = [

    # note: in registering the badgr app at SurfConext, the callback url is explicitely registered on 'openid'
    url('^eduid/login/callback/$', views.callback, name='edu_id_callback'),
    url('^eduid/login/$', views.login, name="edu_id_login")
]