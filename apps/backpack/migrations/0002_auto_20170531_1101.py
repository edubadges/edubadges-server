# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from mainsite.utils import generate_entity_uri


def noop(apps, schema_editor):
    return None


def migrate_localbadgeinstance_badgeinstance(apps, schema_editor):
    LocalBadgeInstance = apps.get_model('composition', 'LocalBadgeInstance')
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    CompositionCollection = apps.get_model('composition', 'Collection')
    BackpackCollection = apps.get_model('backpack', 'BackpackCollection')
    BackpackCollectionBadgeInstance = apps.get_model('backpack', 'BackpackCollectionBadgeInstance')

    # index composition_collection.id -> backpack_collection
    _collection_idx = {}

    # make new backpack collections
    for composition_collection in CompositionCollection.objects.all():
        backpack_collection, created = BackpackCollection.objects.get_or_create(
            created_by=composition_collection.owner,
            slug=composition_collection.slug,
            defaults=dict(
                entity_id=generate_entity_uri(),
                name=composition_collection.name,
                description=composition_collection.description,
                share_hash=composition_collection.share_hash,
            )
        )
        _collection_idx[composition_collection.id] = backpack_collection

    # copy LocalBadgeInstances into BadgeInstance
    for localbadgeinstance in LocalBadgeInstance.objects.all():
        assertion_source = 'composition.localbadgeinstance'
        assertion_original_url = localbadgeinstance.json.get('id')
        try:
            badgeinstance = BadgeInstance.objects.get(
                source=assertion_source,
                source_url=assertion_original_url,
            )
        except BadgeInstance.DoesNotExist:
            badgeinstance = BadgeInstance.objects.create(
                source=assertion_source,
                source_url=assertion_original_url,
                entity_id=generate_entity_uri(),
                created_at=localbadgeinstance.created_at,
                created_by=localbadgeinstance.created_by,
                badgeclass=localbadgeinstance.issuer_badgeclass,
                issuer=localbadgeinstance.issuer_badgeclass.issuer,
                recipient_identifier=localbadgeinstance.recipient_identifier,
                image=localbadgeinstance.image,
                slug=localbadgeinstance.slug,
                revoked=localbadgeinstance.revoked,
                revocation_reason=localbadgeinstance.revocation_reason
            )

        for composition_collect in localbadgeinstance.localbadgeinstancecollection_set.all():
            backpack_collection = _collection_idx.get(composition_collect.collection_id, None)
            if backpack_collection is not None:
                backpack_collect, created = BackpackCollectionBadgeInstance.objects.get_or_create(
                    collection=backpack_collection,
                    badgeinstance=badgeinstance
                )


class Migration(migrations.Migration):

    dependencies = [
        ('backpack', '0001_initial'),
        ('issuer', '0023_auto_20170531_1044'),
        ('composition', '0015_auto_20170420_0649')
    ]

    operations = [
        migrations.RunPython(migrate_localbadgeinstance_badgeinstance, reverse_code=noop)
    ]
