from allauth.account.adapter import get_adapter
from allauth.account.forms import ResetPasswordForm
from allauth.account.utils import filter_users_by_email
from django.core.urlresolvers import reverse, reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic.edit import UpdateView, FormView

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
        email = self.cleaned_data["email"]
        email = get_adapter().clean_email(email)
        return email


class BadgeUserClaim(FormView):
    template_name = 'account/claim.html'
    form_class = UserClaimForm
    success_url = reverse_lazy('account_reset_password_done')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        # if the email address is unknown to us, direct them to the regular signup page
        # otherwise, send them through the forgot-password process to set a password
        form.users = filter_users_by_email(email)
        if len(form.users) < 1:
            self.request.session['signup_email_address'] = email
            return HttpResponseRedirect(reverse('account_signup'))
        elif not form.users[0].password:
            # this account needs to set a password
            form.save(self.request)
            return super(BadgeUserClaim, self).form_valid(form)
        else:
            return HttpResponseRedirect(reverse('account_login'))

