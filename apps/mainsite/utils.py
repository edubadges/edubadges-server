"""
Utility functions and constants that might be used across the project.
"""
from django.apps import apps
from django.conf import settings
from django.core.urlresolvers import get_callable


slugify_function_path = \
    getattr(settings, 'AUTOSLUG_SLUGIFY_FUNCTION', 'autoslug.utils.slugify')

slugify = get_callable(slugify_function_path)

def installed_apps_list():
    installed_apps = []
    for app in ('issuer', 'composer'):
        if apps.is_installed(app):
            installed_apps.append(app)
    return installed_apps
