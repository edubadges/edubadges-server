# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0008_auto_20160322_1404'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeinstance',
            name='acceptance',
            field=models.CharField(default=b'Accepted', max_length=254, choices=[(b'Unaccepted', b'Unaccepted'), (b'Accepted', b'Accepted'), (b'Rejected', b'Rejected')]),
            preserve_default=True,
        ),
    ]
