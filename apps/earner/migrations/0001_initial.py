# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('badgeanalysis', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='EarnerBadge',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('earner_description', models.TextField(blank=True)),
                ('earner_accepted', models.BooleanField(default=False)),
                ('badge', models.ForeignKey(to='badgeanalysis.OpenBadge')),
                ('earner', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
