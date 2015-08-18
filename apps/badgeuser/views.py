from django.core.urlresolvers import reverse
from django.views.generic.edit import UpdateView

from .models import BadgeUser


class UpdateBadgeUserIsActive(UpdateView):
    model = BadgeUser
    fields = ['is_active']
    template_name = 'account/account.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('account_enabled')
