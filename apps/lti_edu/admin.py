from django.contrib import admin

from lti_edu.models import StudentsEnrolled
from mainsite.admin import badgr_admin
from mainsite.utils import admin_list_linkify


@admin.register(StudentsEnrolled)
class StudentsEnrolledAdmin(admin.ModelAdmin):
    list_display = ('date_created', 'date_consent_given',
                    'date_awarded', 'badge_instance',
                    admin_list_linkify('badge_class', 'name'),
                    admin_list_linkify('user', 'full_name'))


badgr_admin.register(StudentsEnrolled, StudentsEnrolledAdmin)
