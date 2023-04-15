import os

included_endpoint_prefixes = [
    '/directaward/create',
    '/directaward/accept',
    '/directaward/revoke-direct-awards',
    '/directaward/resend-direct-awards',
    '/earner/badges',
    '/issuer/create',
    '/issuer/edit',
    '/issuer/delete',
    '/issuer/badgeclasses',
    '/issuer/revoke-assertions',
    '/public/institutions',
    '/public/issuers',
    '/public/badges',
    '/public/assertions',
    '/public/validator'
    '/public/institution'
]

excluded_keywords = ['pubkey', 'baked']


def _included_endpoint(path: str):
    for prefix in included_endpoint_prefixes:
        if path.startswith(prefix):
            return True
    return False


def _contains_excluded_keywords(path):
    for keyword in excluded_keywords:
        if keyword in path:
            return True
    return False


def custom_postprocessing_hook(result, generator, request, public):
    result["security"] = [{"openId": []}],
    result["components"]["securitySchemes"] = {
        "openId": {
            "type": "openIdConnect",
            "openIdConnectUrl": f"{os.environ['EDUID_PROVIDER_URL']}/.well-known/openid-configuration"
        }
    }
    return result


def custom_preprocessing_hook(endpoints):
    new_endpoints = []
    for (path, path_regex, method, callback) in endpoints:
        if _included_endpoint(path) and not _contains_excluded_keywords(path):
            new_endpoints.append((path, path_regex, method, callback))
    return new_endpoints
