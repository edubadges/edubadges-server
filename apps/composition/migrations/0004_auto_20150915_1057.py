# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('composition', '0003_auto_20150914_1447'),
    ]

    operations = [
        migrations.AlterField(
            model_name='localissuer',
            name='image',
            field=models.ImageField(null=True, upload_to=b'uploads/issuers', blank=True),
            preserve_default=True,
        ),
    ]
