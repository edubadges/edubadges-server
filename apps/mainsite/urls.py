from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.shortcuts import redirect
from django.views.generic.base import RedirectView
from mainsite.views import Error404, Error500, SitemapView
from homepage.sitemap import HomeSitemap
from skycms.structure.sitemap import PageSitemap


admin.autodiscover()
#make sure that any view/model/form imports occur AFTER admin.autodiscover

sitemaps = {
    'index': HomeSitemap,
    'pages': PageSitemap,
}

urlpatterns = patterns('',
    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL)),

    # Sitemaps
    url(r'^sitemap$', SitemapView.as_view(), name='sitemap'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),

    # Admin URLs
    # https://github.com/concentricsky/django-client-admin
    url(r'^staff/', include('client_admin.urls')),
    url(r'^staff/', include(admin.site.urls)),

    # Local Apps
    url(r'^contact', include('contact.urls')),
    url(r'^search', include('search.urls')),
    url(r'^badgeanalysis', include('badgeanalysis.urls')),
    url(r'^', include('certificates.urls')),
    url(r'^', include('skycms.structure.urls')),
)


# Test URLs to allow you to see these pages while DEBUG is True
if getattr(settings, 'DEBUG_ERRORS', False):
    urlpatterns = patterns('mainsite.views',
        url(r'^error/404/$', 'error404', name='404'),
        url(r'^error/500/$', 'error500', name='500'),
    ) + urlpatterns

# If DEBUG_MEDIA is set, have django serve anything in MEDIA_ROOT at MEDIA_URL
if getattr(settings, 'DEBUG_MEDIA', True):
    media_url = getattr(settings, 'MEDIA_URL', '/media/').lstrip('/')
    urlpatterns = patterns('',
        url(r'^%s(?P<path>.*)$' % (media_url,), 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT
        }),
    ) + urlpatterns

# If DEBUG_STATIC is set, have django serve up static files even if DEBUG=False
if getattr(settings, 'DEBUG_STATIC', True):
    static_url = getattr(settings, 'STATIC_URL', '/static/').lstrip('/')
    urlpatterns = patterns('',
        url(r'^%s(?P<path>.*)' % (static_url,), 'django.contrib.staticfiles.views.serve', kwargs={
            'insecure': True,
        })
    ) + urlpatterns
