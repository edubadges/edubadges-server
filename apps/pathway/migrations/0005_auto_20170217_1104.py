# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pathway', '0004_pathway_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='pathwayelement',
            name='completion_badgeclass',
            field=models.ForeignKey(related_name='completion_elements', blank=True, to='issuer.BadgeClass', null=True, on_delete=models.SET_NULL),
            preserve_default=True,
        ),
    ]
