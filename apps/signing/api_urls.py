from django.conf.urls import url
from django.views.decorators.clickjacking import xframe_options_exempt
from signing.api import SymmetricKeyListView, SymmetricKeyDetailView, PublicKeyDetailView


urlpatterns = [

    url(r'^password$', SymmetricKeyDetailView.as_view(), name='signing_get_symkey_existance'),
    url(r'^update-password$', SymmetricKeyDetailView.as_view(), name='signing_update_password'),
    url(r'^add-password$', SymmetricKeyListView.as_view(), name='signing_add_password'),
    url(r'^public_key/(?P<entity_id>[^/.]+)$', xframe_options_exempt(PublicKeyDetailView.as_view()), name='signing_public_key_json')
]
