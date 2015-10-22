from allauth.account.forms import ResetPasswordForm
from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import UpdateView, FormView
from django.forms import forms

from .models import BadgeUser


class UpdateBadgeUserIsActive(UpdateView):
    model = BadgeUser
    fields = ['is_active']
    template_name = 'account/account.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('account_enabled')


###
# I had to put this form here because if I put it in badgeuser/forms.py (with the signup form)
# then django-allauth fails the whole server in an import loop on startup
#   --Wiggins
###
class UserClaimForm(ResetPasswordForm):
    """A form for claiming an auto-generated LTI account"""

    def clean_email(self):
        email = super(UserClaimForm, self).clean_email()
        user = self.users[0]
        if user.password:
            raise forms.ValidationError("Account already claimed")
        return email


class BadgeUserClaim(FormView):
    template_name = 'account/claim.html'
    form_class = UserClaimForm
    success_url = reverse_lazy('account_reset_password_done')

    def form_valid(self, form):
        form.save(self.request)
        return super(BadgeUserClaim, self).form_valid(form)

