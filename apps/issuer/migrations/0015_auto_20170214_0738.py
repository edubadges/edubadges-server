# -*- coding: utf-8 -*-


from django.db import migrations


def noop(apps, schema):
    pass


def update_staff_role(apps, schema):
    IssuerStaff = apps.get_model('issuer', 'IssuerStaff')
    Issuer = apps.get_model('issuer', 'Issuer')
    for staff in IssuerStaff.objects.all():
        if staff.editor and staff.role != 'editor':
            staff.role = 'editor'
        staff.save()

    for issuer in Issuer.objects.all():
        new_staff, created = IssuerStaff.objects.get_or_create(issuer=issuer, user=issuer.owner, defaults={
            'role': 'owner'
        })
        new_staff.save()


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0014_issuerstaff_role'),
    ]

    operations = [
        migrations.RunPython(update_staff_role, reverse_code=noop)
    ]
