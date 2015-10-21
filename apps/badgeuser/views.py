from django.core.urlresolvers import reverse, reverse_lazy
from django.views.generic.edit import UpdateView, FormView
from badgeuser.forms import UserClaimForm

from .models import BadgeUser


class UpdateBadgeUserIsActive(UpdateView):
    model = BadgeUser
    fields = ['is_active']
    template_name = 'account/account.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('account_enabled')


class BadgeUserClaim(FormView):
    template_name = 'account/claim.html'
    form_class = UserClaimForm
    success_url = reverse_lazy('account_reset_password_done')

    def form_valid(self, form):
        form.save(self.request)
        return super(BadgeUserClaim, self).form_valid(form)

