from django.db import migrations, models


def copy_description_to_new_columns(apps, schema_editor):
    Institution = apps.get_model('institution', 'Institution')
    for institution in Institution.objects.all():
        institution.description_english = institution.description
        institution.description_dutch = institution.description
        institution.save()
    Faculty = apps.get_model('institution', 'Faculty')
    for faculty in Faculty.objects.all():
        faculty.description_english = faculty.description
        faculty.description_dutch = faculty.description
        faculty.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', '0028_auto_20200808_1221'),
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
