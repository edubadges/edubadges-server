# Generated by Django 3.2.18 on 2023-03-29 10:07

from django.db import migrations, models


def migrate_default_status(apps, schema_editor):
    DirectAwardBundle = apps.get_model('directaward', 'DirectAwardBundle')
    for direct_award_bundle in DirectAwardBundle.objects.all():
        direct_award_bundle.status = 'Active'
        direct_award_bundle.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('directaward', '0011_directaward_warning_email_send'),
    ]

    operations = [
        migrations.AddField(
            model_name='directawardbundle',
            name='scheduled_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='directawardbundle',
            name='status',
            field=models.CharField(choices=[('Scheduled', 'Scheduled'), ('Active', 'Active')], default='Active',
                                   max_length=254),
        ),
        migrations.RunPython(migrate_default_status, reverse_code=noop),
    ]