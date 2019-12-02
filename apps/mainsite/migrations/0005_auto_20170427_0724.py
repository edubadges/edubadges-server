# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0004_auto_20170120_1724'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emailblacklist',
            name='email',
            field=models.EmailField(unique=True, max_length=254),
        ),
    ]
