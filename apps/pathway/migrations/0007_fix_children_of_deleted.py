# -*- coding: utf-8 -*-


from django.db import models, migrations
import autoslug.fields

def noop(apps, schema_editor):
    pass

def mark_children_of_inactive_as_inactive(apps, schema_editor):
    PathwayElement = apps.get_model('pathway', 'PathwayElement')
    Pathway = apps.get_model('pathway', 'Pathway')

    def fix_element(elem, parent_active):
        if not parent_active and elem.is_active:
            elem.is_active = False
            elem.save()

        for child in elem.pathwayelement_set.all():
            fix_element(child, elem.is_active)

    for pathway in Pathway.objects.all():
        root = pathway.root_element
        fix_element(root, root.is_active)


class Migration(migrations.Migration):
    dependencies = [
        ('pathway', '0006_auto_20170413_1054'),
    ]

    operations = [
        migrations.RunPython(mark_children_of_inactive_as_inactive, reverse_code=noop)
    ]
