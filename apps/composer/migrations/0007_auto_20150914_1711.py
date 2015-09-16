# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def copy_collection_to_composition(apps, schema_editor):
    # Import historical version
    ComposerCollection = apps.get_model("composer", "Collection")
    Collection = apps.get_model("composition", "Collection")

    for composer_collection in ComposerCollection.objects.all():
        # Foreign keys

        # Computations for data necessary in LocalIssuer

        # Create composition Collection from composer's Collection data
        new_collection, created = Collection.objects.get_or_create({
            'name': composer_collection.name,
            'slug': composer_collection.slug,
            'description': composer_collection.description,
            'share_hash': composer_collection.share_hash,

            # WARNING: Null-able -> NOT NULL
            'owner': composer_collection.owner,  # Auth user
        }, slug=composer_collection.slug, owner=composer_collection.owner)


def copy_collectionpermission_to_composition(apps, schema_editor):
    # Import historical version
    ComposerCollectionPermission = \
        apps.get_model("composer", "CollectionPermission")
    CollectionPermission = apps.get_model("composition", "CollectionPermission")
    Collection = apps.get_model("composition", "Collection")

    for composer_collectionpermission in \
            ComposerCollectionPermission.objects.all():
        # Foreign keys
        referenced_collection = Collection.objects.get(
            slug=composer_collectionpermission.collection.slug)

        # Create composition CollectionPermission from composer's
        # CollectionPermission data
        new_collectionpermission, created = \
            CollectionPermission.objects.get_or_create({
                # WARNING: Null-able -> NOT NULL
                'can_write': composer_collectionpermission.can_write,
                # WARNING: Foreign key ; Null-able -> NOT NULL
                'user': composer_collectionpermission.user,  # Auth user FK

                # TODO: Foreign key : Collection
                'collection': referenced_collection,
            }, user=composer_collectionpermission.user,
                collection=composer_collectionpermission.collection)


def copy_storedbadgeinstancecollection_to_composition(apps, schema_editor):
    # Import historical version
    ComposerStoredBadgeInstanceCollection = apps.get_model(
        "composer", "StoredBadgeInstanceCollection")
    LocalBadgeInstanceCollection = apps.get_model(
        "composition", "LocalBadgeInstanceCollection")

    LocalBadgeInstance = apps.get_model("composition", "LocalBadgeInstance")
    Collection = apps.get_model("composition", "Collection")

    for storedbadgeinstancecollection in \
            ComposerStoredBadgeInstanceCollection.objects.all():
        # Foreign keys
        referenced_collection = Collection.objects.get(
            slug=storedbadgeinstancecollection.collection.slug)

        storedbadgeinstance = storedbadgeinstancecollection.instance
        referenced_localbadgeinstance = LocalBadgeInstance.objects.get(
            identifier=storedbadgeinstance.url)

        # Create composition LocalBadgeInstanceCollection from composer's
        # LocalBadgeInstanceCollection data
        new_localbadgeinstancecollection, created = \
            LocalBadgeInstanceCollection.objects.get_or_create({
                'description': storedbadgeinstancecollection.description,

                # TODO: Foreign key : LocalBadgeInstance
                'instance': referenced_localbadgeinstance,
                # TODO: Foreign key : Collection
                'collection': referenced_collection,
            }, instance=storedbadgeinstancecollection.instance,
                collection=storedbadgeinstancecollection.collection)


class Migration(migrations.Migration):

    dependencies = [
        ('composer', '0006_auto_20150915_1103'),
        ('composition', '0004_auto_20150915_1057'),
        # credential_store 0004_auto_20150914_2125 below migrates all
        # credential_store.StoredComponents to compostion.LocalComponents.
        # LocalComponents being populated are required for this datamigration.
        ('credential_store', '0004_auto_20150914_2125'),
    ]

    operations = [
        migrations.RunPython(copy_collection_to_composition),
        migrations.RunPython(copy_collectionpermission_to_composition),
        migrations.RunPython(copy_storedbadgeinstancecollection_to_composition),
    ]
