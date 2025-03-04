from django.urls import path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt

from signing.api import SymmetricKeyListView, SymmetricKeyDetailView, PublicKeyIssuerDetailView, SetIssuerSignerView

urlpatterns = [
    path('password', SymmetricKeyDetailView.as_view(), name='signing_get_symkey_existance'),
    path('update-password', SymmetricKeyDetailView.as_view(), name='signing_update_password'),
    path('add-password', SymmetricKeyListView.as_view(), name='signing_add_password'),
    path('set-signer', SetIssuerSignerView.as_view(), name='signing_set_signer'),
    re_path(
        r'^public_key/(?P<entity_id>[^/.]+)$',
        xframe_options_exempt(PublicKeyIssuerDetailView.as_view()),
        name='signing_public_key_json',
    ),
]
