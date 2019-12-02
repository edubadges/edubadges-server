# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0003_auto_20160415_1030'),
        ('recipient', '0002_auto_20160331_1418'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipientgroup',
            name='pathways',
            field=models.ManyToManyField(related_name='recipient_groups', to='pathway.Pathway'),
            preserve_default=True,
        ),
    ]
