# Generated by Django 2.2.24 on 2021-11-17 07:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('issuer', '0096_badgeclass_award_non_validated_name_allowed'),
        ('lti13', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='LtiCourse',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('identifier', models.CharField(max_length=255)),
                ('title', models.CharField(max_length=255)),
                ('label', models.CharField(max_length=255)),
                ('badgeclass', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='lti_course', to='issuer.BadgeClass')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
