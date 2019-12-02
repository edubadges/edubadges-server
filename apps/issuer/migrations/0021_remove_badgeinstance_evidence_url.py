# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0020_auto_20170420_0811'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeinstance',
            name='evidence_url',
        ),
    ]
