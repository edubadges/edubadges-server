from allauth.account.models import EmailAddress
from allauth.socialaccount import providers
from allauth.socialaccount.providers.google.provider import GoogleProvider, GoogleAccount


class UnverifiedGoogleProvider(GoogleProvider):
    id = 'google'
    name = 'Google'
    package = 'allauth.socialaccount.providers.google'
    account_class = GoogleAccount

    def extract_email_addresses(self, data):
        """
        Force verification of email addresses
        """
        ret = []
        email = data.get('email')
        if email and data.get('verified_email'):
            ret.append(EmailAddress(email=email,
                                    verified=False,  # Originally verified=True
                                    primary=True))
        return ret

providers.registry.register(UnverifiedGoogleProvider)
