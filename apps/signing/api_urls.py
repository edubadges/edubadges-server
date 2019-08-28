from django.conf.urls import url
from signing.api import SymmetricKeyView


urlpatterns = [

    url(r'^add-password$', SymmetricKeyView.as_view(), name='signing_add_password'),

]
