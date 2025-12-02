import os
from drf_spectacular.utils import (
    extend_schema,
    inline_serializer,
    OpenApiExample,
    OpenApiResponse,
    OpenApiParameter,
    OpenApiTypes,
)

included_endpoint_prefixes = [
    '/directaward/create',
    '/directaward/bundle',
    '/directaward/accept',
    '/directaward/delete-direct-awards',
    '/directaward/resend-direct-awards',
    '/directaward/revoke-direct-awards',
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
    '/public/validator',
    '/public/institution',
    '/mobile/api',
    '/queries/catalog/badge-classes',
    '/queries/issuers',
    '/queries/faculties',
    '/queries/overview-issuers',
    '/queries/direct-awards',
    '/queries/badge-classes',
    '/queries/users',
    '/queries/notifications',
    '/queries/endorsement-badge-classes',
    '/queries/current-institution',
]

excluded_keywords = ['pubkey', 'baked', 'image']


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
    result['security'] = ([{'openId': []}],)
    url_ = os.environ['EDUID_PROVIDER_URL']
    result['components']['securitySchemes'] = {
        'openId': {'type': 'openIdConnect', 'openIdConnectUrl': f'{url_}/.well-known/openid-configuration'}
    }
    mobile_parameter = {
        'name': 'x-requested-with',
        'schema': {'type': 'string', 'enum': ['mobile']},
        'description': 'x-requested-with header',
        'in': 'header',
        'required': True,
    }
    for path, details in result['paths'].items():
        for method, conf in details.items():
            conf['security'] = [{'openId': ['openid']}]
            if path.startswith('/mobile/'):
                parameters = conf.get('parameters', [])
                parameters.append(mobile_parameter)
                conf['parameters'] = parameters
    return result


def custom_preprocessing_hook(endpoints):
    new_endpoints = []
    for endpoint in endpoints:
        path = endpoint[0]
        if _included_endpoint(path) and not _contains_excluded_keywords(path):
            new_endpoints.append(endpoint)
    return new_endpoints
