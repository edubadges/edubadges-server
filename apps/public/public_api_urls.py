from django.urls import path, re_path
from django.views.decorators.clickjacking import xframe_options_exempt
from rest_framework.urlpatterns import format_suffix_patterns

from .public_api import (
    InstitutionJson,
    InstitutionImage,
    IssuerJson,
    IssuerBadgesJson,
    IssuerImage,
    BadgeClassJson,
    BadgeClassImage,
    BadgeClassCriteria,
    BadgeInstanceJson,
    BadgeInstanceImage,
    BakedBadgeInstanceImage,
    BadgeClassPublicKeyJson,
    IssuerPublicKeyJson,
    AssertionValidate,
    AssertionRecipientName,
    ValidatorVersion,
    FacultyImage,
)

json_patterns = [
    re_path(
        r'^institutions/(?P<entity_id>[^/.]+)$',
        xframe_options_exempt(InstitutionJson.as_view(slugToEntityIdRedirect=True)),
        name='institution_json',
    ),
    re_path(
        r'^issuers/(?P<entity_id>[^/.]+)$',
        xframe_options_exempt(IssuerJson.as_view(slugToEntityIdRedirect=True)),
        name='issuer_json',
    ),
    re_path(
        r'^issuers/(?P<entity_id>[^/.]+)/pubkey/(?P<public_key_id>[^/.]+)$',
        xframe_options_exempt(IssuerPublicKeyJson.as_view(slugToEntityIdRedirect=True)),
        name='issuer_public_key_json',
    ),
    re_path(
        r'^issuers/(?P<entity_id>[^/.]+)/badges$',
        xframe_options_exempt(IssuerBadgesJson.as_view(slugToEntityIdRedirect=True)),
        name='issuer_badges_json',
    ),
    re_path(
        r'^badges/(?P<entity_id>[^/.]+)$',
        xframe_options_exempt(BadgeClassJson.as_view(slugToEntityIdRedirect=True)),
        name='badgeclass_json',
    ),
    re_path(
        r'^badges/(?P<entity_id>[^/.]+)/pubkey/(?P<public_key_id>[^/.]+)$',
        xframe_options_exempt(BadgeClassPublicKeyJson.as_view(slugToEntityIdRedirect=True)),
        name='badgeclass_public_key_json',
    ),
    re_path(
        r'^assertions/(?P<entity_id>[^/.]+)$',
        xframe_options_exempt(BadgeInstanceJson.as_view(slugToEntityIdRedirect=True)),
        name='badgeinstance_json',
    ),
    path(
        'assertions/validate/<str:entity_id>',
        xframe_options_exempt(AssertionValidate.as_view()),
        name='assertion_validate',
    ),
    path(
        'assertions/identity/<str:identity>/<str:salt>',
        xframe_options_exempt(AssertionRecipientName.as_view()),
        name='assertion_recipient_name',
    ),
    path('validator/info', xframe_options_exempt(ValidatorVersion.as_view()), name='validator_info'),
]

image_patterns = [
    path(
        'institution/<str:entity_id>/image',
        InstitutionImage.as_view(slugToEntityIdRedirect=True),
        name='institution_image',
    ),
    path('faculties/<str:entity_id>/image', FacultyImage.as_view(slugToEntityIdRedirect=True), name='faculty_image'),
    path('issuers/<str:entity_id>/image', IssuerImage.as_view(slugToEntityIdRedirect=True), name='issuer_image'),
    re_path(
        r'^badges/(?P<entity_id>[^/]+)/image',
        BadgeClassImage.as_view(slugToEntityIdRedirect=True),
        name='badgeclass_image',
    ),
    re_path(
        r'^badges/(?P<entity_id>[^/]+)/criteria',
        BadgeClassCriteria.as_view(slugToEntityIdRedirect=True),
        name='badgeclass_criteria',
    ),
    re_path(
        r'^assertions/(?P<entity_id>[^/]+)/image',
        BadgeInstanceImage.as_view(slugToEntityIdRedirect=True),
        name='badgeinstance_image',
    ),
    re_path(
        r'^assertions/(?P<entity_id>[^/]+)/baked',
        BakedBadgeInstanceImage.as_view(slugToEntityIdRedirect=True),
        name='badgeinstance_bakedimage',
    ),
]

urlpatterns = format_suffix_patterns(json_patterns, allowed=['json']) + image_patterns
