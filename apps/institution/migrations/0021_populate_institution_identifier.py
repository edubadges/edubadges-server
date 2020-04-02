from django.db import migrations


def populate_institution_identifier(apps, schema_editor):
    Institution = apps.get_model('institution', 'Institution')
    for institution in Institution.objects.all():
        institution.identifier = institution.name
        institution.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', '0020_institution_identifier'),
    ]

    operations = [
        migrations.RunPython(populate_institution_identifier, reverse_code=noop)
    ]
