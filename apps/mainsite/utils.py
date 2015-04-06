"""
Utility functions and constants that might be used across the project.
"""
from django.conf import settings

# Slugify function
from django.core.urlresolvers import get_callable
slugify_function_path = getattr(settings, 'AUTOSLUG_SLUGIFY_FUNCTION', 'autoslug.utils.slugify')
slugify = get_callable(slugify_function_path)