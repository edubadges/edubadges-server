from django.db import migrations


def set_badgeuser_is_teacher(apps, schema_editor):
    BadgeUser = apps.get_model('badgeuser', 'BadgeUser')
    try:
        SocialAccount = apps.get_model('socialaccount', 'SocialAccount')

        for user in BadgeUser.objects.all():
            try:
                social_account = SocialAccount.objects.get(user=user)
                if social_account.provider == 'surf_conext':
                    user.is_teacher = True
                    user.save()
            except SocialAccount.DoesNotExist:
                pass
    except LookupError:  # initial migration
        pass

def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('badgeuser', '0049_badgeuser_is_teacher'),
    ]

    operations = [
        migrations.RunPython(set_badgeuser_is_teacher, reverse_code=noop)
    ]
