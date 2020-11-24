from django.db import migrations, models


def copy_description_to_new_columns(apps, schema_editor):
    Issuer = apps.get_model('issuer', 'Issuer')
    for issuer in Issuer.objects.all():
        issuer.description_english = issuer.description
        issuer.description_dutch = issuer.description
        issuer.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('issuer', '0074_auto_20201013_1219')
    ]

    operations = [
        migrations.AddField(
            model_name='issuer',
            name='description_english',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='issuer',
            name='description_dutch',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.RunPython(copy_description_to_new_columns, reverse_code=noop)
    ]
