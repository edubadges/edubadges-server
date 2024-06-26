# Generated by Django 3.2.24 on 2024-04-15 09:13

from django.db import migrations


def migrate_institutions_micro_credentials_enabled(apps, schema_editor):
    Institution = apps.get_model('institution', 'Institution')
    BadgeClass = apps.get_model('issuer', 'BadgeClass')
    all_micro_credential_institutions = list(
        BadgeClass.objects.values('issuer__faculty__institution_id').filter(is_micro_credentials=True).distinct().all())
    for row in all_micro_credential_institutions:
        institution = Institution.objects.get(id=row['issuer__faculty__institution_id'])
        institution.micro_credentials_enabled = True
        institution.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', '0054_badgeclasstag'),
    ]

    operations = [
        migrations.RunPython(migrate_institutions_micro_credentials_enabled, reverse_code=noop)
    ]
