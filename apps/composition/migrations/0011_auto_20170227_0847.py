# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0010_auto_20170214_0712'),
    ]

    operations = [
        migrations.RenameField(
            model_name='localbadgeinstance',
            old_name='badgeclass',
            new_name='local_badgeclass',
        ),
        migrations.RenameField(
            model_name='localbadgeinstance',
            old_name='issuer',
            new_name='local_issuer',
        ),
    ]
