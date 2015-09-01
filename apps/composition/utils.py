import hashlib
import re
import json

from rest_framework.serializers import ValidationError

from verifier.utils import (get_badge_instance_from_baked_image,
                            get_badge_instance_from_json,
                            get_badge_component_from_url)


def get_verified_badge_instance_from_form(validated_data):
    if 'image' in validated_data:
        return get_badge_instance_from_baked_image(validated_data['image'])

    if 'assertion' in validated_data and validated_data.get('assertion'):
        return get_badge_instance_from_json(validated_data['assertion'])

    if 'url' in validated_data:
        return get_badge_component_from_url(validated_data['url'])

    raise ValidationError(
        "No badge instance found from the given form input.")


def _get_reference_type(component_reference):
    try:
        component_reference = json.loads(component_reference)
    except Exception:
        pass

    if isinstance(component_reference, dict):
        return ("json", component_reference)

    if re.match(r"^http", component_reference):
        return ("url", component_reference)

    if component_reference.count('.') == 2:
        return ("jws", component_reference)


def _get_email_type(badge_instance):
    recipient = badge_instance['recipient']
    if isinstance(recipient, dict):
        email_type = recipient.get('hashed') and "hash" or "email"
        return (email_type, recipient['identity'], recipient.get('salt', ''))

    if re.match(r"^([^$]+\$)?[0-9a-f]+$", recipient):
        return ("hash", recipient, badge_instance.get('salt'))

    if re.match(r"^[^@]+@[^.]+\..+$", recipient):
        return ("email", recipient, None)


def badge_email_matches_emails(badge_instance, verified_addresses):
    email_type, badge_email, salt = _get_email_type(badge_instance)

    if email_type == "email":
        return badge_email in verified_addresses

    if email_type == "hash":
        try:
            hash_algorithm, hash_string = badge_email.split('$')
        except ValueError:
            return False  # No algoirthm, no matching hash.

        # TODO: Ensure hash is one of two possibilities or return False

        for email in verified_addresses:
            algorithm_func = hashlib.new(hash_algorithm)
            algorithm_func.update(salt)
            algorithm_func.update(email.email)
            if (hash_string == algorithm_func.hexdigest()):
                return True

    return False
