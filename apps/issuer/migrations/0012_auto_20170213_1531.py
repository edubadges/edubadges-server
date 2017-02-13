# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.db import migrations

from mainsite.utils import OriginSetting


def noop(apps, schema_editor):
    return None


def deserialize_issuer_json(apps, schema_editor):
    Issuer = apps.get_model('issuer', 'Issuer')
    for issuer in Issuer.objects.all():
        issuer.description = issuer.old_json.get('description')
        issuer.email = issuer.old_json.get('email')
        issuer.url = issuer.old_json.get('url')
        issuer.save()


def deserialize_badgeclass_json(apps, schema_editor):
    BadgeClass = apps.get_model('issuer', 'BadgeClass')
    for badgeclass in BadgeClass.objects.all():
        badgeclass.description = badgeclass.old_json.get('description')

        criteria_url = badgeclass.old_json.get('criteria_url')

        local_criteria_url = OriginSetting.HTTP+reverse('badgeclass_criteria', kwargs={'slug': badgeclass.slug})
        if criteria_url != local_criteria_url:
            badgeclass.criteria_url = criteria_url

        badgeclass.save()


def deserialize_badgeinstance_json(apps, schema_editor):
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    for instance in BadgeInstance.objects.all():
        recipient = instance.old_json.get('recipient')
        if not isinstance(recipient, basestring) and 'salt' in recipient:
            instance.salt = recipient.get('salt')

        evidence = instance.old_json.get('evidence')
        if evidence:
            instance.evidence_url = evidence

        instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0011_auto_20170213_1531'),
    ]

    operations = [
        migrations.RunPython(deserialize_issuer_json, reverse_code=noop),
        migrations.RunPython(deserialize_badgeclass_json, reverse_code=noop),
        migrations.RunPython(deserialize_badgeinstance_json, reverse_code=noop)
    ]
