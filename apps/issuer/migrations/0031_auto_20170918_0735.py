# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-09-18 14:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0030_badgeclassalignment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='badgeinstance',
            name='recipient_type',
            field=models.CharField(choices=[('email', 'email'), ('id', 'id'), ('telephone', 'telephone'), ('url', 'url')], default='email', max_length=255),
        ),
    ]