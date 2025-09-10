import logging
from rest_framework.exceptions import APIException
from badgeuser.models import BadgeUser

class RevalidatedNameException(APIException):
    pass

class NoValidatedNameException(APIException):
    pass

def process_eduid_response(eduid_response: dict, user: BadgeUser):
    logger = logging.getLogger('Badgr.Debug')

    validated_names = [info['validated_name'] for info in eduid_response if 'validated_name' in info]

    user.clear_affiliations()
    for info in eduid_response:
        if 'eppn' in info and 'schac_home_organization' in info:
            user.add_affiliations([{'eppn': info['eppn'].lower(),
                                    'schac_home': info['schac_home_organization'], }])
            logger.info(f'Stored affiliations {info["eppn"]} {info["schac_home_organization"]}')

    if user.validated_name and len(validated_names) == 0:
        raise RevalidatedNameException
    if len(validated_names) > 0:
        # Use the preferred linked account for the validated_name.
        preferred_validated_name = [info['validated_name'] for info in eduid_response if info['preferred']]
        if not preferred_validated_name:
            # This should never happen as it would be a bug in eduID, but let's be defensive
            preferred_validated_name = [validated_names[0]]
        user.validated_name = preferred_validated_name[0]
    else:
        user.validated_name = None
        raise NoValidatedNameException
