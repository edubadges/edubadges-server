from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """A simple management command which clears the site-wide cache."""

    help = "Fully clear your site-wide cache."

    def handle(self, *args, **kwargs):
        assert settings.CACHES, "The CACHES setting is not configured!"
        cache.clear()
        self.stdout.write("Your cache has been cleared!\n")
