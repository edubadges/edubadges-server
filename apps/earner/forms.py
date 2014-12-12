from django import forms
from earner.models import EarnerBadge


class EarnerBadgeCreateForm(forms.ModelForm):

    class Meta:
        model = EarnerBadge
        exclude = []
