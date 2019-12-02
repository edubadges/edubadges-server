

from django.db import migrations

def reverse_func(apps, schema_editor):
    StudentsEnrolled = apps.get_model('lti_edu', 'StudentsEnrolled')
    for studentsenrolled in StudentsEnrolled.objects.all():
        studentsenrolled.badge_instance = None
        studentsenrolled.save()


def forwards_func(apps, schema_editor):
    StudentsEnrolled = apps.get_model('lti_edu', 'StudentsEnrolled')
    BadgeInstance = apps.get_model('issuer', 'BadgeInstance')
    for studentsenrolled in StudentsEnrolled.objects.all():
        try:
            badge_instance = BadgeInstance.objects.get(entity_id=studentsenrolled.assertion_slug)
            studentsenrolled.badge_instance = badge_instance
            studentsenrolled.save()
        except BadgeInstance.DoesNotExist:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('lti_edu', '0020_studentsenrolled_badge_instance'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]