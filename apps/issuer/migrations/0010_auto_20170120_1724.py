# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0009_badgeinstance_acceptance'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeinstance',
            name='acceptance',
            field=models.CharField(default=b'Unaccepted', max_length=254, choices=[(b'Unaccepted', b'Unaccepted'), (b'Accepted', b'Accepted'), (b'Rejected', b'Rejected')]),
            preserve_default=True,
        ),
    ]
