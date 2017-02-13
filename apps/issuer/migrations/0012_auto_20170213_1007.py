# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

from issuer.models import Issuer, BadgeClass


def deserialize_issuer_json(apps, schema_editor):
    for issuer in Issuer.objects.all():
        issuer.description = issuer.json.get('description')
        issuer.email = issuer.json.get('email')
        issuer.url = issuer.json.get('url')
        issuer.save()


def deserialize_badgeclass_json(apps, schema_editor):
    for badgeclass in BadgeClass.objects.all():
        badgeclass.description = badgeclass.json.get('description')

        criteria_url = badgeclass.json.get('criteria_url')
        if criteria_url != badgeclass.get_full_url():
            badgeclass.criteria_url = criteria_url

        badgeclass.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0011_auto_20170213_1007'),
    ]

    operations = [
        migrations.RunPython(deserialize_issuer_json),
        migrations.RunPython(deserialize_badgeclass_json)
    ]
