# Generated by Django 2.2.9 on 2020-04-15 15:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0066_remove_badgeinstance_narrative'),
    ]

    operations = [
        migrations.AddField(
            model_name='badgeclass',
            name='expiration_period',
            field=models.DurationField(null=True),
        ),
    ]