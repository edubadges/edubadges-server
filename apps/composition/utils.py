import hashlib
import json
import os
import re
import uuid

from django.core.files.base import ContentFile

from openbadges_bakery import bake, unbake
import requests
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
        if badge_email in [e.email for e in verified_addresses]:
            return badge_email
        else:
            return False

    if email_type == "hash":
        try:
            hash_algorithm, hash_string = badge_email.split('$')
        except ValueError:
            return False  # No algoirthm, no matching hash.

        # TODO: Ensure hash is one of two possibilities or return False

        for email in verified_addresses:
            algorithm_func = hashlib.new(hash_algorithm)
            algorithm_func.update(email.email)
            algorithm_func.update(salt)
            if (hash_string == algorithm_func.hexdigest()):
                return email.email

    return False


def use_or_bake_badge_instance_image(uploaded_image, badge_instance,
                                     badge_class):
    # Create a baked badge instance, or use a provided baked badge instance
    # from the form, and assign it to our badge instance in the database.
    if uploaded_image and verify_baked_image(uploaded_image):
        baked_badge_instance = uploaded_image  # InMemoryUploadedFile
    else:
        baked_badge_instance = bake_badge_instance(
            badge_instance, badge_class['image'])  # ContentFile
    # Normalize filename
    _, image_extension = os.path.splitext(baked_badge_instance.name)
    baked_badge_instance.name = \
        'local_badgeinstance_' + str(uuid.uuid4()) + image_extension
    return baked_badge_instance


def verify_baked_image(uploaded_image):
    try:
        unbake(uploaded_image)
    except Exception:
        return False

    return True


def bake_badge_instance(badge_instance, badge_class_image_url):
    try:
        unbaked_image = ContentFile(
            requests.get(badge_class_image_url)._content, "unbaked_image.png")
        unbaked_image.open()
        baked_image = bake(unbaked_image, json.dumps(badge_instance, indent=2))
    except requests.exceptions.RequestException as e:
        raise ValidationError(
            "Error retrieving image {}: {}".format(
                badge_class_image_url, e.message))
    return baked_image
