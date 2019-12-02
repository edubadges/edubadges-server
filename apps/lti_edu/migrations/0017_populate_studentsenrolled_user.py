

from django.db import migrations

def reverse_func(apps, schema_editor):
    StudentsEnrolled = apps.get_model('lti_edu', 'StudentsEnrolled')
    for studentsenrolled in StudentsEnrolled.objects.all():
        studentsenrolled.user = None
        studentsenrolled.save()


def forwards_func(apps, schema_editor):
    StudentsEnrolled = apps.get_model('lti_edu', 'StudentsEnrolled')
    SocialAccount = apps.get_model('socialaccount', 'SocialAccount')
    for studentsenrolled in StudentsEnrolled.objects.all():
        try:
            socialaccount = SocialAccount.objects.get(uid=studentsenrolled.edu_id)
            studentsenrolled.user = socialaccount.user
            studentsenrolled.save()
        except SocialAccount.DoesNotExist:
            studentsenrolled.delete()  # remove enrollments of non existing users after db corruptio

class Migration(migrations.Migration):
    dependencies = [
        ('socialaccount', '__first__'),
        ('lti_edu', '0016_studentsenrolled_user'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]