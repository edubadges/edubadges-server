from django.db import migrations


def populate_invited(apps, schema_editor):
    BadgeUser = apps.get_model('badgeuser', 'BadgeUser')
    for user in BadgeUser.objects.filter(is_teacher=True):
        user.invited = True
        user.save()

def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0058_badgeuser_invited')
    ]

    operations = [
        migrations.RunPython(populate_invited, reverse_code=noop)
    ]

