from django import forms
from django.contrib import admin
from mainsite.admin import badgr_admin

from .models import Theme, get_current_templates


class ThemeForm(forms.ModelForm):

    class Meta:
        model = Theme
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ThemeForm, self).__init__(*args, **kwargs)
        self.fields['terms_and_conditions_template'].widget = forms.Select(choices=get_current_templates())
        self.fields['terms_and_conditions_template_en'].widget = forms.Select(choices=get_current_templates())


class ThemeAdmin(admin.ModelAdmin):
    form = ThemeForm


badgr_admin.register(Theme, ThemeAdmin)
