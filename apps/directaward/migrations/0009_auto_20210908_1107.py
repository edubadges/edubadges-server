# Generated by Django 2.2.24 on 2021-09-08 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('directaward', '0008_directaward_revocation_reason'),
    ]

    operations = [
        migrations.AddField(
            model_name='directaward',
            name='description',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='directaward',
            name='evidence_url',
            field=models.CharField(blank=True, default=None, max_length=2083, null=True),
        ),
        migrations.AddField(
            model_name='directaward',
            name='name',
            field=models.CharField(blank=True, default=None, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='directaward',
            name='narrative',
            field=models.TextField(blank=True, default=None, null=True),
        ),
    ]
