# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0002_auto_20160331_1443'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='pathwayelementbadge',
            options={'ordering': ('ordering',)},
        ),
        migrations.AddField(
            model_name='pathwayelementbadge',
            name='ordering',
            field=models.IntegerField(default=99),
            preserve_default=True,
        ),
    ]
