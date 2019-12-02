# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0013_auto_20170214_0711'),
    ]

    operations = [
        migrations.AddField(
            model_name='issuerstaff',
            name='role',
            field=models.CharField(default='staff', max_length=254, choices=[('owner', 'Owner'), ('editor', 'Editor'), ('staff', 'Staff')]),
            preserve_default=True,
        ),
    ]
