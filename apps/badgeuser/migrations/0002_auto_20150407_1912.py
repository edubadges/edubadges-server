# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='badgeuser',
            name='name',
        ),
        migrations.RemoveField(
            model_name='badgeuser',
            name='short_name',
        ),
        migrations.AddField(
            model_name='badgeuser',
            name='first_name',
            field=models.CharField(default='First Name', max_length=30, verbose_name='first name', blank=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='badgeuser',
            name='last_name',
            field=models.CharField(default='Last Name', max_length=30, verbose_name='last name', blank=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='badgeuser',
            name='email',
            field=models.EmailField(max_length=75, verbose_name='email address', blank=True),
            preserve_default=True,
        ),
    ]
