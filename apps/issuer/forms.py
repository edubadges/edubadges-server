from django import forms
from issuer.models import EarnerNotification, Issuer


class IssuerForm(forms.ModelForm):

    class Meta:
        model = Issuer
        exclude = []


class NotifyEarnerForm(forms.ModelForm):

    class Meta:
        model = EarnerNotification
        exclude = []

    def clean_url(self):
        try:
            EarnerNotification.objects.get(url=self.cleaned_data['url'])

        except EarnerNotification.DoesNotExist:
            pass
        else:
            raise forms.ValidationError(
                "The earner of this assertion has already been notified: %(url)s",
                code='invalid',
                params={'url': self.cleaned_data['url']}
            )
        return self.cleaned_data['url']
