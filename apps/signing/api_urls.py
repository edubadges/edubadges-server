from django.conf.urls import url
from signing.api import SymmetricKeyView


urlpatterns = [

    url(r'^add-password$', SymmetricKeyView.as_view(), name='signing_add_password'),
    url(r'^password$', SymmetricKeyView.as_view(), name='signing_get_symkey_existance'),

]
