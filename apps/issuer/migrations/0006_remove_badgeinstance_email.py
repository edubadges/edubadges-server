# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0005_auto_20150915_1723'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeinstance',
            name='email',
        ),
    ]
