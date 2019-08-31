from django.conf.urls import url
from signing.api import SymmetricKeyListView, SymmetricKeyDetailView


urlpatterns = [

    url(r'^password$', SymmetricKeyDetailView.as_view(), name='signing_get_symkey_existance'),
    url(r'^update-password$', SymmetricKeyDetailView.as_view(), name='signing_update_password'),
    url(r'^add-password$', SymmetricKeyListView.as_view(), name='signing_add_password'),

]
