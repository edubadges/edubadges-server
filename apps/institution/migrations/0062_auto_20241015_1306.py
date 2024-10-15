# Generated by Django 3.2.25 on 2024-10-15 11:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0061_auto_20241015_0915'),
    ]

    operations = [
        migrations.AddField(
            model_name='faculty',
            name='visibility_type',
            field=models.CharField(blank=True, choices=[('PUBLIC', 'PUBLIC'), ('TEST', 'TEST')], max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='institution',
            name='institution_type',
            field=models.CharField(blank=True, choices=[('WO', 'WO'), ('HBO', 'HBO'), ('MBO', 'MBO'), ('HBO/MBO', 'HBO/MBO'), ('SURF', 'SURF')], max_length=254, null=True),
        ),
    ]