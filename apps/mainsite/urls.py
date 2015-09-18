from django.apps import apps
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from .views import SitemapView, info_view, email_unsubscribe


admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

TOKEN_REGEX = '(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})'

sitemaps = {
}

urlpatterns = patterns('',
    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL)),

    # Pattern library & Temp Views
    url(r'^pattern-library$', TemplateView.as_view(template_name='pattern-library.html'), name='pattern-library'),
    url(r'^temp/app$', TemplateView.as_view(template_name='temp-app.html'), name='temp-app'),
    url(r'^temp/canvas$', TemplateView.as_view(template_name='temp-canvas.html'), name='temp-canvas'),

    # Home
    url(r'^$', info_view, name='index'),

    # Sitemaps
    url(r'^sitemap$', SitemapView.as_view(), name='sitemap'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),

    # Admin URLs from client_admin
    # https://github.com/concentricsky/django-client-admin
    url(r'^staff/', include('client_admin.urls')),
    url(r'^staff/', include(admin.site.urls)),

    # accounts:
    url(r'^accounts[/]?$', RedirectView.as_view(url='/accounts/email/')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe, name='unsubscribe'),
    url(r'^login', RedirectView.as_view(url='/accounts/login', permanent=False, query_string=True), name='login'),
    url(r'^logout', RedirectView.as_view(url='/accounts/logout', permanent=False), name='logout'),

    # REST Framework-based APIs
    url(r'^user', include('badgeuser.urls')),
    url(r'^v1/user', include('badgeuser.api_urls')),

    url(r'^public', include('issuer.public_api_urls')),

    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^docs/', include('rest_framework_swagger.urls')),

    # Service health endpoint
    url(r'^health', include('health.urls')),

)

if apps.is_installed('issuer'):
    urlpatterns += patterns('',
        url(r'^v1/$', RedirectView.as_view(url='/v1/issuer/issuers', permanent=False)),
        url(r'^v1/issuer', include('issuer.api_urls')),
        url(r'^issuer', include('issuer.urls')),
    )

if apps.is_installed('composition'):
    urlpatterns += patterns('',
        url(r'^v1/earner', include('composition.api_urls')),
        url(r'^earner', include('composition.urls')),
    )

if apps.is_installed('badgebook'):
    urlpatterns += patterns('',
        url(r'^accounts/lti$', 'badgebook.views.lti_info', name='badgebook_lti_info'),
        url(r'^v1/badgebook', include('badgebook.api_urls')),
        url(r'^badgebook', include('badgebook.urls')),
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
