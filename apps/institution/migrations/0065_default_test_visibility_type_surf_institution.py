# Generated by Django 3.2.25 on 2024-11-04 09:11

from django.db import migrations


def populate_faculty_visibility_type(apps, schema_editor):
    Faculty = apps.get_model('institution', 'Faculty')
    for faculty in Faculty.objects.filter(institution__identifier__icontains='surf'):
        faculty.visibility_type = 'TEST'
        faculty.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('institution', '0064_Institution_default_support_for_virtual_organisations'),
    ]

    operations = [
        migrations.RunPython(populate_faculty_visibility_type, reverse_code=noop)
    ]