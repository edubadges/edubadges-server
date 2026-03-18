from rest_framework.exceptions import AuthenticationFailed
from badgrsocialauth.providers.eduid.provider import EduIDProvider


def sync_user_with_eduid(user, eduid_data, logger):
    validated_names = []
    preferred_name = None

    user.clear_affiliations()

    for info in eduid_data:
        # validated names
        if "validated_name" in info:
            validated_names.append(info["validated_name"])
            if info.get("preferred"):
                preferred_name = info["validated_name"]

        # affiliations
        if "eppn" in info and "schac_home_organization" in info:
            user.add_affiliations([{
                "eppn": info["eppn"].lower(),
                "schac_home": info["schac_home_organization"],
            }])

    if not validated_names:
        user.validated_name = None
        return

    user.validated_name = preferred_name or validated_names[0]


def extract_bearer_token(request) -> str:
    auth = request.headers.get("Authorization", "")

    if not auth.lower().startswith("bearer "):
        raise AuthenticationFailed("Invalid or missing Authorization header")

    return auth.split(" ", 1)[1]


def provision_user_from_temporary(request, temp_user):
    provider = EduIDProvider(request)
    social_login = provider.sociallogin_from_response(
        request,
        temp_user.user_payload
    )
    social_login.save(request)
    return social_login.user
