from django.db import migrations


def populate_institution_identifier(apps, schema_editor):
    InstitutionStaff = apps.get_model('staff', 'InstitutionStaff')
    BadgeUser = apps.get_model('badgeuser', 'BadgeUser')
    for user in BadgeUser.objects.all():
        if user.is_teacher:
            try:
                staff = InstitutionStaff.objects.get(user=user)
                user.institution = staff.institution
                user.save()
            except InstitutionStaff.DoesNotExist:
                pass



def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0052_badgeuser_institution')
    ]

    operations = [
        migrations.RunPython(populate_institution_identifier, reverse_code=noop)
    ]

