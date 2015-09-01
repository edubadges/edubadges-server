from base64 import b64decode
import json
import re
from urlparse import urlparse

from jwt import api_jws, InvalidTokenError
from openbadges_bakery import unbake
from rest_framework.serializers import ValidationError
import requests

import serializers


def domain(url):
    return urlparse(url).netloc


def get_badge_instance_from_baked_image(baked_image):
    image_data = unbake(baked_image)
    badge_instance_type = _get_reference_type(image_data)

    if badge_instance_type == "json":
        return get_badge_instance_from_json(image_data)
    if badge_instance_type == "url":
        return get_badge_component_from_url(image_data)
    if badge_instance_type == "jwt":
        return get_badge_instance_from_jwt(image_data)

    raise ValidationError(
        "Unable to determine badge instance format from baked image.")


def find_and_get_badge_class(badge_reference):
    badge_class_type = _get_reference_type(badge_reference)

    if badge_class_type == "dict":
        return json.loads(badge_reference)

    if badge_class_type == "url":
        return get_badge_component_from_url(badge_reference)


def find_and_get_issuer(issuer_reference):
    issuer_type = _get_reference_type(issuer_reference)

    if issuer_type == "dict":
        return json.loads(issuer_reference)

    if issuer_type == "url":
        return get_badge_component_from_url(issuer_reference)


def get_badge_instance_from_json(json_data):
    json_data = json.loads(json_data)

    if json_data['verify']['type'] == 'signed':
        raise ValidationError(
            "A signed badge instance must be received via JWT string, not \
            JSON.")
    url = json_data['verify']['url']
    return get_badge_component_from_url(url)


def get_badge_component_from_url(url):
    badge_component = _fetch(url)
    return badge_component


def get_badge_instance_from_jwt(jwt_string):
    (header, payload, signature,) = jwt_string.split('.')
    algorithm = json.loads(b64decode(header))['alg'].upper()

    badge_instance = json.loads(b64decode(payload))
    if badge_instance['verify']['type'] == 'hosted':
        raise ValidationError(
            "A signed badge instance must be validated via public key not \
            hosted.")
    url = badge_instance['verify']['url']
    public_key = _fetch(url)

    try:
        payload = api_jws.decode(jwt_string, public_key,
                                 algorithm=algorithm)
    except InvalidTokenError:
        raise ValidationError(
            "The signed badge instance did not validate against its public \
            key.")

    badge_instance = badge_instance
    return badge_instance


def _fetch(url):
    return requests.get(url, headers={'Accept': 'application/json'}).json()


def _get_reference_type(component_reference):
    try:
        component_reference = json.loads(component_reference)
    except Exception:
        pass

    if isinstance(component_reference, dict):
        return "json"

    if re.match(r"^http", component_reference):
        return "url"

    if component_reference.count('.') == 2:
        return "jwt"
