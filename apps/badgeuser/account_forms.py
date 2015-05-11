from django import forms

from allauth.account import forms as allauth_forms


class AddEmailForm(allauth_forms.AddEmailForm):
    email = forms.EmailField(
        label="email", required=True,
        widget=forms.TextInput(attrs={"type": "email", "size": "30"})
    )
