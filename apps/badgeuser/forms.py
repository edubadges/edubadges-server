from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django import forms

from .models import BadgeUser


class BadgeUserCreationForm(UserCreationForm):
    """
    A form that creates a user, with no privileges, from the given email and
    password.
    """

    class Meta:
        model = BadgeUser
        fields = ("email", "first_name", "last_name")

    def signup(self, request, user):
        pass


class BadgeUserChangeForm(UserChangeForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    password hash display field.
    """

    class Meta:
        model = BadgeUser
        exclude = []


