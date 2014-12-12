from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext_lazy as _

from models import BadgeUser
from forms import BadgeUserChangeForm, BadgeUserCreationForm


class BadgeUserAdmin(UserAdmin):
    # The forms to add and change user instances

    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference the removed 'username' field
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('name', 'short_name', 'email',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                       'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')
            }),
    )
    form = BadgeUserChangeForm
    add_form = BadgeUserCreationForm
    list_display = ('username', 'email', 'name', 'short_name', 'is_staff')
    search_fields = ('username', 'email', 'name', 'short_name')
    ordering = ('username',)

admin.site.register(BadgeUser, BadgeUserAdmin)
