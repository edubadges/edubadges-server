# -*- coding: utf-8 -*-


from django.db import migrations


def copy_email_into_recipient_identifier(apps, schema_editor):
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    for badgeinstance in BadgeInstance.objects.all():
        badgeinstance.recipient_identifier = badgeinstance.email
        badgeinstance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0004_auto_20150915_1722'),
    ]

    operations = [
        migrations.RunPython(copy_email_into_recipient_identifier)
    ]
