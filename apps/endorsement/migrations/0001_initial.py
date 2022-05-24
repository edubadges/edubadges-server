# Generated by Django 2.2.26 on 2022-05-23 14:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('issuer', '0100_auto_20220509_1338'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Endorsement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('entity_id', models.CharField(default=None, max_length=254, unique=True)),
                ('claim', models.TextField(blank=True, default=None, null=True)),
                ('description', models.TextField(blank=True, default=None, null=True)),
                ('status', models.CharField(choices=[('Unaccepted', 'Unaccepted'), ('Accepted', 'Unaccepted'), ('Revoked', 'Revoked'), ('Rejected', 'Rejected')], default='Unaccepted', max_length=254)),
                ('revocation_reason', models.CharField(blank=True, default=None, max_length=512, null=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('endorsee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='endorsees', to='issuer.BadgeClass')),
                ('endorser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='endorsements', to='issuer.BadgeClass')),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
