# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def migrate_duplicate_collection_badges(apps, schema_editor):
    LocalBadgeInstanceCollection = apps.get_model('composition.LocalBadgeInstanceCollection')
    BadgeInstance = apps.get_model('issuer.BadgeInstance')
    for entry in LocalBadgeInstanceCollection.objects.all():
        if entry.instance_id:
            try:
                issuer_instance = BadgeInstance.objects.get(slug=entry.instance.json.get('uid'))
            except BadgeInstance.DoesNotExist:
                pass
            else:
                old_instance_id = entry.instance_id
                entry.issuer_instance = issuer_instance
                entry.instance = None

                print("Migrating duplicate badge Collection.pk={}: LocalBadgeInstance.pk={} -> BadgeInstance.slug={}".format(
                    entry.collection_id, old_instance_id, issuer_instance.slug
                ))
                entry.save()


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0008_collectionshare_localbadgeinstanceshare'),
        ('issuer', '0009_badgeinstance_acceptance'),
    ]

    operations = [
        migrations.RunPython(migrate_duplicate_collection_badges)
    ]
