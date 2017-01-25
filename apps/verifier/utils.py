from base64 import b64decode
import itertools
import json
import re
import simplejson
from urlparse import urlparse

from jwt import api_jws, InvalidTokenError
from openbadges_bakery import unbake
from rest_framework.serializers import ValidationError
import requests


def domain(url):
    return urlparse(url).netloc

def merge_details(new_detail, old_detail):
    if not isinstance(new_detail, (list, tuple,)):
        new_detail = [new_detail]
    if not isinstance(old_detail, (list, tuple,)):
        old_detail = [old_detail]

    return list(itertools.chain(new_detail, old_detail))



def get_badge_instance_from_baked_image(baked_image):
    image_data = unbake(baked_image)

    if not image_data:
        raise ValidationError(
            "No badge data found within the provided image.")

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
        return (None, badge_reference)

    if badge_class_type == "url":
        try:
            return get_badge_component_from_url(badge_reference)
        except ValidationError as e:
            raise ValidationError(merge_details(
                "Error attempting to retrieve the hosted BadgeClass file: {}"
                .format(badge_reference),
                e.detail
            ))


def find_and_get_issuer(issuer_reference):
    issuer_type = _get_reference_type(issuer_reference)

    if issuer_type == "dict":
        return (None, issuer_reference)

    if issuer_type == "url":
        try:
            return get_badge_component_from_url(issuer_reference)
        except ValidationError as e:

            raise ValidationError(merge_details(
                "Error attempting to retrieve the hosted Issuer file: {}"
                .format(issuer_reference),
                e.detail
            ))


def get_badge_instance_from_json(json_data):
    json_data = json.loads(json_data)

    if not json_data.get('verify'):
        return (None, json_data)  # v0.5 badges have no reference to fetch.

    if json_data['verify']['type'] == 'signed':
        raise ValidationError(
            "A signed badge instance must be received via JWT string, not JSON.")
    url = json_data['verify']['url']
    return get_badge_component_from_url(url)


def get_badge_component_from_url(url, **kwargs):
    if 'preloaded_response' in kwargs:
        badge_component = kwargs.get('preloaded_response').json()
    else:
        try:
            badge_component = _fetch(url)
        except requests.exceptions.RequestException as e:
            raise ValidationError(
                "Unable to fetch a badge component: {}"
                .format(e.message)
            )
        except simplejson.JSONDecodeError:
            raise ValidationError(
                "Unable to find a valid json component at url: {}"
                .format(url)
            )
    return (url, badge_component)


def get_badge_instance_from_jwt(jwt_string):
    (header, payload, signature,) = jwt_string.split('.')
    algorithm = json.loads(b64decode(header))['alg'].upper()

    badge_instance = json.loads(b64decode(payload))
    if badge_instance['verify']['type'] == 'hosted':
        raise ValidationError(
            "A signed badge instance must be validated via public key not hosted.")
    url = badge_instance['verify']['url']
    public_key = _fetch(url)

    try:
        payload = api_jws.decode(jwt_string, public_key,
                                 algorithm=algorithm)
    except InvalidTokenError:
        raise ValidationError(
            "The signed badge instance did not validate against its public key.")

    badge_instance = badge_instance
    return (None, badge_instance)


def _fetch(url):
    return requests.get(url, headers={'Accept': 'application/json'}).json()


def _get_reference_type(component_reference):
    try:
        component_reference = json.loads(component_reference)
        return "json"
    except Exception:
        pass

    if isinstance(component_reference, dict):
        return "dict"

    if re.match(r"^http", component_reference):
        return "url"

    if component_reference.count('.') == 2:
        return "jwt"


def normalize_error_message(error):
    """
    Some ValidationErrors have a message that is an array. This will ensure there is not a double-nested array.
    :return str
    """
    if isinstance(error, list):
        return "; ".join(error)
    return error
