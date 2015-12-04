# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from urlparse import urlparse

from django.db import models, migrations
from django.core.files.base import ContentFile
from django.forms.models import model_to_dict

import requests

from composition.utils import use_or_bake_badge_instance_image


def copy_storedissuer_to_composition(apps, schema_editor):
    # Import historical version
    StoredIssuer = apps.get_model("credential_store", "StoredIssuer")
    LocalIssuer = apps.get_model("composition", "LocalIssuer")

    for storedissuer in StoredIssuer.objects.all():
        # Computations for data necessary in LocalIssuer
        storedissuer_name = storedissuer.json['name']

        # Create LocalIssuer from StoredIssuer data
        new_localissuer, created = LocalIssuer.objects.get_or_create({
            'json': storedissuer.json,
            'identifier': storedissuer.url,
            'image': None,  # Null-able

            # TODO: Generate ; NOT NULL
            'name': storedissuer_name,

            # TODO: REMOVE!
            # 'slug': None,
        }, identifier=storedissuer.url)


def copy_storedbadgeclass_to_composition(apps, schema_editor):
    # Import historical version
    StoredBadgeClass = apps.get_model("credential_store", "StoredBadgeClass")
    LocalBadgeClass = apps.get_model("composition", "LocalBadgeClass")
    LocalIssuer = apps.get_model("composition", "LocalIssuer")

    for storedbadgeclass in StoredBadgeClass.objects.all():
        # Computations for data necessary in LocalIssuer
        storedbadgeclass_name = storedbadgeclass.json['name']

        image_url = storedbadgeclass.json['image']
        # TODO: Detect appropriate extension if necessary
        filename = urlparse(image_url).path[1:].replace('/', '-') + ".png"

        try:
            storedbadgeclass_image = ContentFile(
                requests.get(image_url)._content, filename)
        except requests.exceptions.ConnectionError:
            print "Unable to reach BadgeClass image at:", image_url
            storedbadgeclass_image = ContentFile('', filename)

        # Foreign keys
        referenced_localissuer = LocalIssuer.objects.get(
            identifier=storedbadgeclass.issuer.url)

        # Create LocalIssuer from StoredIssuer data
        new_localbadgeclass, created = LocalBadgeClass.objects.get_or_create({
            'json': storedbadgeclass.json,
            'identifier': storedbadgeclass.url,

            # TODO: Generate ; NOT NULL
            'name': storedbadgeclass_name,
            # TODO: Null-able -> NOT NULL
            'image': storedbadgeclass_image,

            # TODO: Foreign key
            'issuer': referenced_localissuer,

            # TODO: REMOVE!
            # 'slug': None,
        }, identifier=storedbadgeclass.url)


def copy_storedbadgeinstance_to_composition(apps, schema_editor):
    # Import historical version
    StoredBadgeInstance = apps.get_model("credential_store",
                                         "StoredBadgeInstance")
    LocalBadgeInstance = apps.get_model("composition", "LocalBadgeInstance")
    LocalBadgeClass = apps.get_model("composition", "LocalBadgeClass")
    LocalIssuer = apps.get_model("composition", "LocalIssuer")

    for storedbadgeinstance in StoredBadgeInstance.objects.all():
        # Foreign keys
        try:
            referenced_localbadgeclass = LocalBadgeClass.objects.get(
                identifier=storedbadgeinstance.badgeclass.url)
            badgeclass_as_dict = model_to_dict(referenced_localbadgeclass)
        except AttributeError:  # V0.5 badge
            referenced_localbadgeclass = None
            badgeclass_as_dict = storedbadgeinstance.json['badge']
            print "Found a V0.5 badge, baking an image with nested badge:\n", \
                storedbadgeinstance.json['badge']


        try:
            referenced_localissuer = LocalIssuer.objects.get(
                identifier=storedbadgeinstance.issuer.url)
        except AttributeError:  # V0.5 badge
            referenced_localissuer = None

        # Computations for data necessary in LocalIssuer
        image_url = storedbadgeinstance.json['image']
        # TODO: Detect appropriate extension if necessary
        filename = urlparse(image_url).path.split('/')[-1] + ".png"

        try:
            storedbadgeinstance_image = ContentFile(
                requests.get(image_url)._content, filename)
        except requests.exceptions.ConnectionError:
            print "Unable to reach BadgeInstance image at:", image_url
            storedbadgeinstance_image = ContentFile('', filename)

        baked_image = use_or_bake_badge_instance_image(
            storedbadgeinstance_image,
            model_to_dict(storedbadgeinstance),
            badgeclass_as_dict)

        # Create LocalIssuer from StoredIssuer data
        new_localbadgeinstance, created = \
            LocalBadgeInstance.objects.get_or_create({
                'json': storedbadgeinstance.json,
                'identifier': storedbadgeinstance.url,
                'recipient_identifier': storedbadgeinstance.recipient_id,
                'recipient_user': storedbadgeinstance.recipient_user,  # TODO: FK

                # TODO: BAKE ONE! ; Null-able -> NOT NULL
                'image': baked_image,

                # TODO: Foreign key
                'badgeclass': referenced_localbadgeclass,
                # TODO: Foreign key
                'issuer': referenced_localissuer,
            }, identifier=storedbadgeinstance.url)


class Migration(migrations.Migration):

    dependencies = [
        ('credential_store', '0003_storedbadgeinstance_image'),
        ('composition', '0004_auto_20150915_1057'),
    ]

    operations = [
        migrations.RunPython(copy_storedissuer_to_composition),
        migrations.RunPython(copy_storedbadgeclass_to_composition),
        migrations.RunPython(copy_storedbadgeinstance_to_composition),
    ]
