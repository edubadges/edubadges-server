from django.urls import re_path
from ob3.api import CredentialsView

# The OID4VCI protocol endpoints (`.well-known/*`, `auth/token`,
# `openid4vci/credential`, ...) used to be proxied here to the OB3 agent.
# They are now served directly and publicly by the ssi-agent service itself
# so wallets talk to it directly. Just the offer needs to be created from here.
urlpatterns = [
    re_path(r"^v1/ob3", CredentialsView.as_view(), name="verifiable_credentials"),
]
