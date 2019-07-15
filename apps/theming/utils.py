
from mainsite.models import BadgrApp
from theming.models import Theme


def get_theme(request):
    badgr_app = BadgrApp.objects.get_current(request)
    try:
        return badgr_app.theme
    except Theme.DoesNotExist as e:
        return None