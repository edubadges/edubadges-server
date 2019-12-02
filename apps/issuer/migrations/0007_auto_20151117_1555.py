# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0006_remove_badgeinstance_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeclass',
            name='image',
            field=models.FileField(upload_to=b'uploads/badges', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='badgeinstance',
            name='image',
            field=models.FileField(upload_to=b'uploads/badges', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='issuer',
            name='image',
            field=models.FileField(null=True, upload_to=b'uploads/issuers', blank=True),
            preserve_default=True,
        ),
    ]
