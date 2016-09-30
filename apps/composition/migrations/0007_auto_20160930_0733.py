# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0009_badgeinstance_acceptance'),
        ('composition', '0006_auto_20160928_0648'),
    ]

    operations = [
        migrations.AddField(
            model_name='localbadgeinstancecollection',
            name='issuer_instance',
            field=models.ForeignKey(to='issuer.BadgeInstance', null=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localbadgeinstancecollection',
            name='collection',
            field=models.ForeignKey(related_name='badges', to='composition.Collection'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='localbadgeinstancecollection',
            name='instance',
            field=models.ForeignKey(to='composition.LocalBadgeInstance', null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='localbadgeinstancecollection',
            unique_together=set([('instance', 'issuer_instance', 'collection')]),
        ),
    ]
