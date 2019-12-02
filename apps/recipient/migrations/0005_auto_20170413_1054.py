# -*- coding: utf-8 -*-


from django.db import models, migrations
import autoslug.fields


class Migration(migrations.Migration):

    dependencies = [
        ('recipient', '0004_auto_20160511_1024'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipientgroup',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'name', unique=True, max_length=254, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recipientgroupmembership',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'populate_slug', unique=True, max_length=254, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='recipientprofile',
            name='slug',
            field=autoslug.fields.AutoSlugField(populate_from=b'recipient_identifier', unique=True, max_length=254, editable=False),
            preserve_default=True,
        ),
    ]
