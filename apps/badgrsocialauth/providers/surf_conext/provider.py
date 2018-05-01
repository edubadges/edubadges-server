try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse
from allauth.account.models import EmailAddress
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider, ProviderAccount

from badgeuser.models import BadgeUser
from badgrsocialauth.adapter import BadgrSocialAccountAdapter


class SurfConextProvider(Provider):
    """
    Overrides common patterns that assist in callback function
    """

    id = 'surf_conext'
    name = 'SURFconext'
    package = 'badgrsocialauth.providers.surf_conext'
    account_class = ProviderAccount

    def extract_uid(self, response):
        return response['sub']

    def extract_extra_data(self, response):
        return response

    def extract_email_addresses(self, data, user=None):
        # Force verification of email addresses because SurfConext will only transmit verified emails
        return [EmailAddress(email=data['email'].strip().lower(),
                             verified=True,
                             primary=True)]

    def extract_common_fields(self, data):
        # extracts data required to build user model
        return dict(email=data['email'],
                    first_name=data.get('given_name', None),
                    last_name=data.get('family_name', None)
                    )


providers.registry.register(SurfConextProvider)
