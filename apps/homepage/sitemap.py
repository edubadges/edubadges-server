from django.contrib.sitemaps import Sitemap
from homepage.models import HomePage


class HomeSitemap(Sitemap):
    changefreq = "daily"
    priority = 1

    def items(self):
        return HomePage.objects.filter(is_active=True)
    def location(self, obj):
        return '/'
    def lastmod(self, obj):
        return obj.updated_at