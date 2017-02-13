# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from issuer.models import BadgeInstance


def deserialize_badgeinstance_json(apps, schema_editor):
    for instance in BadgeInstance.objects.all():
        recipient = instance.json.get('recipient')
        if not isinstance(recipient, basestring) and 'salt' in recipient:
            instance.salt = recipient.get('salt')

        evidence = instance.json.get('evidence')
        if evidence:
            instance.evidence_url = evidence

        instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0013_auto_20170213_1025'),
    ]

    operations = [
        migrations.RunPython(deserialize_badgeinstance_json),
    ]
