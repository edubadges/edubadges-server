from allauth.socialaccount.admin import SocialAccountAdmin

from badgeuser.models import StudentAffiliation


class BadgrSocialAccountAdmin(SocialAccountAdmin):
    list_display = ('user', '_eduid', 'eppn', 'provider', 'date_joined')
    readonly_fields = ('_eduid',)
    exclude = ('uid',)

    def _eduid(self, obj):
        return obj.uid

    def eppn(self, obj):
        student_affiliations = StudentAffiliation.objects.filter(user=obj.user).all()
        return ", ".join([s.eppn for s in student_affiliations]) if student_affiliations else None

    _eduid.short_description = 'EduID'
