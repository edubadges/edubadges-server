# Generated by Django 3.2.24 on 2024-07-19 13:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mainsite', '0019_auto_20210416_1512'),
    ]

    operations = [
        migrations.CreateModel(
            name='SystemNotification',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification', models.TextField(default=None)),
                ('display_start', models.DateTimeField(auto_now_add=True)),
                ('display_end', models.DateTimeField(auto_now_add=True)),
                ('notification_type', models.CharField(choices=[('warning', 'warning'), ('info', 'info')], default='info', max_length=254)),
            ],
        ),
    ]
