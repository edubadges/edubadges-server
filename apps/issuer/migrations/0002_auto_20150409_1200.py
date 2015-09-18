# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='issuerstaff',
            old_name='badgeuser',
            new_name='user',
        ),
        migrations.AlterUniqueTogether(
            name='issuerstaff',
            unique_together=set([('issuer', 'user')]),
        ),
    ]
