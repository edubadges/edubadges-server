import json
import requests

from django.core.files.base import ContentFile

from allauth.account.models import EmailAddress
from rest_framework.exceptions import ValidationError

from bakery import bake, unbake


def find_recipient_user(recipient_id):
    try:
        confirmed_email = EmailAddress.objects.get(
            email=recipient_id, verified=True
        )
    except EmailAddress.DoesNotExist:
        return None
    else:
        return confirmed_email.user


def baked_image_from_abi(abi):
    image_url = abi.badge_instance.get('image')
    if image_url is not None:
        try:
            image = requests.get(image_url)

            unbake(image)
        except:
            pass
        else:
            return image

    try:
        image_url = abi.badge.get('image')
        unbaked_image = ContentFile(
            requests.get(image_url)._content, "unbaked_image.png"
        )

        unbaked_image.open()
        baked_image = bake(
            unbaked_image, json.dumps(dict(abi.badge_instance), indent=2)
        )
    except requests.exceptions.SSLError as e:
        raise ValidationError("SSL failure retrieving image " + image_url)
    except Exception as e:
        raise e
    else:
        return baked_image
