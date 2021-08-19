# Generated by Django 2.2.18 on 2021-08-18 11:01

import json

from django.db import migrations
from django.db.models import Q


def migrate_studyload_time_investment(apps, _):
    Institution = apps.get_model('institution', 'Institution')
    for institution in Institution.objects.filter(~Q(institution_type='MBO')):
        for faculty in institution.faculty_set.all():
            for issuer in faculty.issuer_set.all():
                for badge_class in issuer.badgeclasses.filter(formal=True):
                    for ext in badge_class.badgeclassextension_set.filter(name='extensions:StudyLoadExtension'):
                        ext.name = 'extensions:TimeInvestmentExtension'
                        original_obj = json.loads(ext.original_json)
                        original_obj['type'] = ['Extension', 'extensions:TimeInvestmentExtension']
                        context = original_obj['@context']
                        original_obj['@context'] = context.replace('StudyLoadExtension', 'TimeInvestmentExtension')
                        original_obj['TimeInvestment'] = original_obj['StudyLoad']
                        del original_obj['StudyLoad']
                        ext.original_json = json.dumps(original_obj)
                        ext.save()
                        badge_class.formal = False
                        badge_class.save()

class Migration(migrations.Migration):
    dependencies = [
        ('issuer', '0092_auto_20210609_1457'),
    ]

    operations = [
        migrations.RunPython(migrate_studyload_time_investment, reverse_code=migrations.RunPython.noop)
    ]