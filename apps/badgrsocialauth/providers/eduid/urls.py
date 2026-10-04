from django.urls import path, re_path

from . import views

urlpatterns = [
    # note: in registering the badgr app at SurfConext, the callback url is explicitly registered
    path("eduid/login/callback/", views.callback, name="edu_id_callback"),
    path("eduid/login/", views.login, name="edu_id_login"),
    re_path(
        "^eduid/login/terms_accepted/(?P<state>[^/]+)/(?P<id_token>[^/]+)/(?P<access_token>[^/]+)",
        views.after_terms_agreement,
        name="eduid_terms_accepted_callback",
    ),
]
