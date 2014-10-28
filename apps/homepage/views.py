from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from homepage.models import HomePage
from mainsite.views import ActiveTabMixin


class HomeIndexView(ActiveTabMixin, TemplateView):
    template_name = 'homepage/index.html'
    active_tab = 'home'

    def get_context_data(self, **kwargs):
        context = super(HomeIndexView, self).get_context_data(**kwargs)
        homepage_id = self.request.GET.get('id', None)
        if homepage_id and self.request.user.is_staff:
            context['object'] = get_object_or_404(HomePage, id=homepage_id)
        else:
            context['object'] = HomePage.active_objects.active()
        return context
