# -*- coding: utf-8 -*-


from django.db import models, migrations
from django.db.migrations import RunPython


def noop(apps, schema):
    pass


def migrate_evidence_url_to_badgeinstanceevidence(apps, schema):
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    BadgeInstanceEvidence = apps.get_model('issuer', 'BadgeInstanceEvidence')
    for assertion in BadgeInstance.objects.all():
        if assertion.evidence_url:
            evidence, created = BadgeInstanceEvidence.objects.get_or_create(
                badgeinstance=assertion,
                evidence_url=assertion.evidence_url)


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0019_auto_20170420_0810'),
    ]

    operations = [
        RunPython(migrate_evidence_url_to_badgeinstanceevidence, reverse_code=noop)
    ]
