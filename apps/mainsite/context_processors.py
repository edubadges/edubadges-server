from django.conf import settings

def help_email(request):
    return {'HELP_EMAIL': getattr(settings, 'HELP_EMAIL', 'help@badgr.io')}