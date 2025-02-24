from django.urls import path

from . import views

urlpatterns = [
    # note: in registering the badgr app at SurfConext, the callback url is explicitly registered on 'openid'
    path('openid/login/callback/', views.callback, name='surf_conext_callback'),
    path('openid/login/', views.login, name='surf_conext_login'),
]
