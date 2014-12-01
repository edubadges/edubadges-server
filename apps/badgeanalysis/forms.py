from django import forms
from django.forms.widgets import HiddenInput
import json
from badgeanalysis.utils import fetch_linked_component

from certificates.models import Certificate
from badgeanalysis.models import OpenBadge, BadgeScheme


class BadgeSchemeForm(forms.ModelForm):

    class Meta:
        model = BadgeScheme
        exclude = ()

    def clean(self):
        if self.cleaned_data['context_json'] is None:
            self.cleaned_data['context_json'] = fetch_linked_component(self.cleaned_data['context_url']) 

        self.cleaned_data = super(BadgeSchemeForm, self).clean()

        if not self.cleaned_data['default_type'] in ('assertion', 'badgeclass', 'issuerorg', 'extension'):
            self.cleaned_data['default_type'] = 'assertion'


      return self.cleaned_data

    def post_save(self):
        BadgeScheme.registerValidators(self, self['context_json'])
