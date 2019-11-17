from django.conf.urls import url
from django.views.decorators.clickjacking import xframe_options_exempt
from signing.api import SymmetricKeyListView, SymmetricKeyDetailView, PublicKeyIssuerDetailView, SetIssuerSignerView


urlpatterns = [

    url(r'^password$', SymmetricKeyDetailView.as_view(), name='signing_get_symkey_existance'),
    url(r'^update-password$', SymmetricKeyDetailView.as_view(), name='signing_update_password'),
    url(r'^add-password$', SymmetricKeyListView.as_view(), name='signing_add_password'),
    url(r'^set-signer$', SetIssuerSignerView.as_view(), name='signing_set_signer'),
    url(r'^public_key/(?P<entity_id>[^/.]+)$', xframe_options_exempt(PublicKeyIssuerDetailView.as_view()), name='signing_public_key_json')
]
