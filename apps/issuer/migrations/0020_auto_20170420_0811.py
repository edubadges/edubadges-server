# -*- coding: utf-8 -*-


from django.db import migrations
from django.db.migrations import RunPython


def noop(apps, schema):
    pass



class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0019_auto_20170420_0810'),
    ]

    operations = [
        RunPython(noop, reverse_code=noop)
    ]
