from django.db import migrations


def populate_badgeclass_formal(apps, schema_editor):
    BadgeClass = apps.get_model('issuer', 'BadgeClass')
    for badgeclass in BadgeClass.objects.all():
        extensions = badgeclass.badgeclassextension_set.all()
        badgeclass.formal = False
        for extention in extensions:
            if extention.name == 'extensions:ECTSExtension' or extention.name == 'extensions:StudyLoadExtension':
                badgeclass.formal = True
        badgeclass.save()

def noop(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('issuer', '0071_badgeclass_formal'),
    ]

    operations = [
        migrations.RunPython(populate_badgeclass_formal, reverse_code=noop)
    ]
