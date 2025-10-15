import logging
import requests

from django.conf import settings

logger = logging.getLogger('Badgr.Debug')


class OidcClient:
    """
    This class is used to store the openid connect authorization server metadata.
    """

    def __init__(self):
        self._userinfo_endpoint = None
        self._introspect_endpoint = None

    @staticmethod
    def get_client_from_settings():
        provider_name = settings.EDUID_OIDC_PROVIDER_NAME

        if provider_name == 'eduid':
            return EduIdOidcClient()
        elif provider_name == 'surfconext':
            return SurfConextOidcClient()
        else:
            raise Exception(f'Unknown provider name {provider_name}')

    def get_userinfo(self, access_token):
        """
        This function is used to get the userinfo from the OIDC provider.
        It is used to get the userinfo from the OIDC provider.
        """
        if not self._userinfo_endpoint:
            raise Exception('Userinfo endpoint not set')
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
        logger.debug(f'Calling userinfo endpoint {self._userinfo_endpoint}')
        response = requests.get(self._userinfo_endpoint, headers=headers)
        logger.debug(f'Userinfo response - Status Code: {response.status_code}, Headers: {dict(response.headers)}, Content: {response.text}')
        if response.status_code != 200:
            raise Exception(f'User info endpoint error (http {response.status_code}). Try alternative login methods')

        return self.normalize_userinfo(response.json())

    def normalize_userinfo(self, userinfo):
        """
        This function is used to normalize the userinfo from the OIDC provider.
        It is used to get the userinfo from the OIDC provider.
        """
        raise NotImplementedError('This function should be implemented in the subclass')


class EduIdOidcClient(OidcClient):
    """
    Overrides the userinfo endpoint for the eduid provider.
    """

    def __init__(self):
        super().__init__()
        # Here is the issue, we should not connect to eduID!
        self._userinfo_endpoint = f'{settings.EDUID_API_BASE_URL}/myconext/api/eduid/links'
        self._introspect_endpoint = None

    def normalize_userinfo(self, userinfo):
        return EduIdUserInfo(userinfo)


class SurfConextOidcClient(OidcClient):
    """
    Overrides the userinfo endpoint for the surfconext provider.

    The actual endpoints should be fetched from https://connect.test.surfconext.nl/oidc/.well-known/openid-configuration
    """

    def __init__(self):
        super().__init__()
        self._userinfo_endpoint = f'{settings.EDUID_PROVIDER_URL}/userinfo'
        self._introspect_endpoint = f'{settings.EDUID_PROVIDER_URL}/introspect'

    def normalize_userinfo(self, userinfo):
        return SurfConextUserInfo(userinfo)


class UserInfo:
    """
    This class is used to store the userinfo from the OIDC provider.
    """

    def __init__(self):
        self._validated_names = []

    def has_validated_name(self):
        """
        This function is used to check if the user has a validated name.
        """
        return bool(self.validated_names())

    def validated_names(self):
        """
        This function is used to get the validated names from the userinfo.
        """
        raise NotImplementedError('This function should be implemented in the subclass')

    def validated_name(self):
        """
        This function is used to get a canonical validated name from the validated names
        """
        return self.validated_names()[0] if self.validated_names() else None

    def eppn(self):
        """
        This function is used to get the eppn from the userinfo.
        """
        raise NotImplementedError('This function should be implemented in the subclass')

    def schac_home_organization(self):
        """
        This function is used to get the schac_home_organization from the userinfo.
        """
        raise NotImplementedError('This function should be implemented in the subclass')


class EduIdUserInfo(UserInfo):
    """
    This class is used to store the userinfo from the eduid myconext api endpoint.
    """

    def __init__(self, eppn_json):
        super().__init__()

        for info in eppn_json:
            if not info.get('preferred', False):
                continue
            if not 'validated_name' in info:
                continue

            self._validated_names.append(info['validated_name'])

        self._eppn = [info['eppn'] for info in eppn_json if 'eppn' in info]
        self._schac_home_organization = [
            info['schac_home_organization'] for info in eppn_json if 'schac_home_organization' in info
        ]

    def validated_names(self):
        return self._validated_names

    def eppn(self):
        return self._eppn[0] if self._eppn else None

    def schac_home_organization(self):
        return self._schac_home_organization[0] if self._schac_home_organization else None


class SurfConextUserInfo(UserInfo):
    """
    This class is used to store the userinfo from the surfconext api endpoint.
    """

    def __init__(self, userinfo):
        super().__init__()
        ## How do we get the validated name from the surfconext userinfo?
        self._validated_names = [userinfo.get('name', None)]
        self._eppn = userinfo.get('eduperson_principal_name', None)
        self._schac_home_organization = userinfo.get('schac_home_organization', None)

    def validated_names(self):
        return self._validated_names

    def eppn(self):
        return self._eppn

    def schac_home_organization(self):
        return self._schac_home_organization
