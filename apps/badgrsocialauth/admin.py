from allauth.socialaccount.admin import SocialAccountAdmin


class BadgrSocialAccountAdmin(SocialAccountAdmin):
    list_display = ('user', '_eduid', 'provider', 'date_joined')
    readonly_fields = ('_eduid', )
    exclude = ('uid',)

    def _eduid(self, obj):
        return obj.uid

    _eduid.short_description = 'EduID'
