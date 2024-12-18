# Generated by Django 3.2.25 on 2024-10-17 12:10

from django.db import migrations


def populate_institution_virtual_organization_allowed(apps, schema_editor):
    Institution = apps.get_model('institution', 'Institution')
    for institution in Institution.objects.all():
        institution.virtual_organization_allowed = True
        institution.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', '0063_alter_institution_virtual_organization_allowed'),
    ]

    operations = [
        migrations.RunPython(populate_institution_virtual_organization_allowed, reverse_code=noop)
    ]
