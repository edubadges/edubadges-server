# Generated by Django 3.2.24 on 2024-07-22 13:41

from django.db import migrations


def migrate_studyload_to_time_investment_badge_class_extension(apps, schema_editor):
    BadgeClassExtension = apps.get_model('issuer', 'BadgeClassExtension')
    non_wo_studyload_extensions = BadgeClassExtension.objects \
        .exclude(badgeclass__issuer__faculty__institution__institution_type='MBO') \
        .filter(name="extensions:StudyLoadExtension").all()
    for ext in non_wo_studyload_extensions:
        ext.original_json = ext.original_json.replace("StudyLoad", "TimeInvestment")
        ext.name = "extensions:TimeInvestmentExtension"
        ext.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('issuer', '0115_migrate_microcredentials_frameworks_to_quality_assurance'),
    ]

    operations = [
        migrations.RunPython(migrate_studyload_to_time_investment_badge_class_extension, reverse_code=noop)
    ]
