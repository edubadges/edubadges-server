# Generated by Django 3.2.25 on 2024-11-15 13:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0065_default_test_visibility_type_surf_institution'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='email',
            field=models.CharField(blank=True, default=None, max_length=254, null=True),
        ),
    ]