# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0022_merge'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeinstance',
            name='source',
            field=models.CharField(default='local', max_length=254),
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='source_url',
            field=models.CharField(default=None, max_length=254, null=True, blank=True),
        ),
    ]
