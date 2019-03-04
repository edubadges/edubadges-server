from django.contrib.sites.models import Site

from mainsite.models import BadgrApp

def get_theme(request):
    badgr_app = BadgrApp.objects.get_current(request)
    theme = badgr_app.theme
    return theme