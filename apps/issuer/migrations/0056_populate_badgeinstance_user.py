from django.db import migrations


def populate_badgeinstance_user(apps, schema_editor):
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    SocialAccount = apps.get_model('socialaccount', 'SocialAccount')
    for instance in BadgeInstance.objects.all():
        identifier = instance.recipient_identifier
        if identifier.startswith('urn:mace:eduid'):
            try:
                account = SocialAccount.objects.get(uid=identifier)
                instance.user = account.user
                instance.save()
            except SocialAccount.DoesNotExist:
                pass

def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('issuer', '0055_badgeinstance_user'),
    ]

    operations = [
        migrations.RunPython(populate_badgeinstance_user, reverse_code=noop)
    ]
