# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_email_max_length'),
        ('badgeuser', '0004_merge'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailAddressVariant',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.EmailField(max_length=75)),
                ('canonical_email', models.ForeignKey(to='badgeuser.CachedEmailAddress')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ProxyEmailConfirmation',
            fields=[
            ],
            options={
                'verbose_name': 'email confirmation',
                'proxy': True,
                'verbose_name_plural': 'email confirmations',
            },
            bases=('account.emailconfirmation',),
        ),
        migrations.AlterModelOptions(
            name='cachedemailaddress',
            options={'verbose_name': 'email address', 'verbose_name_plural': 'email addresses'},
        ),
    ]
