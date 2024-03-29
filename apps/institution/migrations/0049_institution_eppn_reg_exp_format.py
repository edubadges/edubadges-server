# Generated by Django 2.2.26 on 2022-08-16 11:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('institution', '0048_auto_20220413_0849'),
    ]

    operations = [
        migrations.AddField(
            model_name='institution',
            name='eppn_reg_exp_format',
            field=models.CharField(blank=True, default=None, help_text='A regular expression which defines the EPPN of an institution (e.g. .*@tempguestidp.edubadges.nl)', max_length=255, null=True),
        ),
    ]
