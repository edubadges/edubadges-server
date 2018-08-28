import os
import requests
from base64 import b64encode
from allauth.account.models import EmailAddress
from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import Provider, ProviderAccount
from django.conf import settings

class EduIDProvider(Provider):
    """
    Overrides common patterns that assist in callback function
    """
    id = 'edu_id'
    name = 'EduId'
    package = 'badgrsocialauth.providers.eduid'
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


providers.registry.register(EduIDProvider)
