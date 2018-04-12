from django.conf import settings


def extra_settings(request):
    return {
        'HELP_EMAIL': getattr(settings, 'HELP_EMAIL', 'help@badgr.io'),
        'PINGDOM_MONITORING_ID': getattr(settings, 'PINGDOM_MONITORING_ID', None),
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None),
        'BADGR_UI_URL': getattr(settings, 'BADGR_UI_URL', 'https://badgr.io/')
    }
