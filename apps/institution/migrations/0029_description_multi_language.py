from django.db import migrations, models


def copy_description_to_new_columns(apps, schema_editor):
    Institution = apps.get_model('institution', 'Institution')
    for institution in Institution.objects.all():
        institution.description_english = institution.description
        institution.description_dutch = institution.description
        institution.save()
    Issuer = apps.get_model('issuer', 'Issuer')
    for issuer in Issuer.objects.all():
        issuer.description_english = issuer.description
        issuer.description_dutch = issuer.description
        issuer.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', 'issuer'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='description_english',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='institution',
            name='description_dutch',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='faculty',
            name='description_english',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='faculty',
            name='description_dutch',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.RunPython(copy_description_to_new_columns, reverse_code=noop)
    ]
