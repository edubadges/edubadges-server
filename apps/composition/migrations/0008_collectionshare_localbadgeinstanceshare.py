# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0009_badgeinstance_acceptance'),
        ('composition', '0007_auto_20160930_0733'),
    ]

    operations = [
        migrations.CreateModel(
            name='CollectionShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=254, choices=[(b'facebook', b'Facebook'), (b'linkedin', b'LinkedIn')])),
                ('collection', models.ForeignKey(to='composition.Collection', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='LocalBadgeInstanceShare',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('provider', models.CharField(max_length=254, choices=[(b'facebook', b'Facebook'), (b'linkedin', b'LinkedIn')])),
                ('instance', models.ForeignKey(to='composition.LocalBadgeInstance', null=True, on_delete=models.SET_NULL)),
                ('issuer_instance', models.ForeignKey(to='issuer.BadgeInstance', null=True, on_delete=models.SET_NULL)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
