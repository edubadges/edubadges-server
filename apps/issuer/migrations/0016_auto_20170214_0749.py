# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0015_auto_20170214_0738'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='issuer',
            name='owner',
        ),
        migrations.RemoveField(
            model_name='issuerstaff',
            name='editor',
        ),
    ]
