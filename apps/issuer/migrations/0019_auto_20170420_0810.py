# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0018_auto_20170413_1054'),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeInstanceEvidence',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('evidence_url', models.CharField(max_length=2083)),
                ('narrative', models.TextField(default=None, null=True, blank=True)),
                ('badgeinstance', models.ForeignKey(to='issuer.BadgeInstance')),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='badgeinstance',
            name='narrative',
            field=models.TextField(default=None, null=True, blank=True),
            preserve_default=True,
        ),
    ]
