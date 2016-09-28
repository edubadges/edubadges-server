from allauth.account.views import confirm_email
from django.apps import apps
from django.conf.urls import patterns, include, url
from django.conf import settings
from django.contrib import admin
from django.views.generic.base import RedirectView, TemplateView

from rest_framework.authtoken.views import obtain_auth_token

from .views import SitemapView, info_view, email_unsubscribe, AppleAppSiteAssociation

from mainsite.admin import badgr_admin
badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

TOKEN_REGEX = '(?P<uidb36>[0-9A-Za-z]{1,13})-(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})'

sitemaps = {
}

urlpatterns = patterns('',
    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL)),

    # Home
    url(r'^$', info_view, name='index'),

    # Sitemaps
    url(r'^sitemap$', SitemapView.as_view(), name='sitemap'),
    url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemaps}),

    # Admin URLs
    url(r'^staff/', include(badgr_admin.urls)),

    # accounts:
    url(r'^accounts[/]?$', RedirectView.as_view(url='/accounts/email/')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe, name='unsubscribe'),
    url(r'^login', RedirectView.as_view(url='/accounts/login', permanent=False, query_string=True), name='login'),
    url(r'^logout', RedirectView.as_view(url='/accounts/logout', permanent=False), name='logout'),

    # this URL route exists to satisfy running the legacy frontend signup pages.
    # to be expunged when legacy frontend is removed
    url(r"^legacy/confirm-email/(?P<key>\w+)/$", confirm_email, name="legacy_confirm_email"),

    # REST Framework-based APIs
    url(r'^user', include('badgeuser.urls')),
    url(r'^v1/user', include('badgeuser.api_urls')),
    url(r'^api-auth/token$', obtain_auth_token),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(r'^public', include('issuer.public_api_urls')),

    url(r'^docs/', include('rest_framework_swagger.urls')),

    # Service health endpoint
    url(r'^health', include('health.urls')),

    # Apple app universal URL endpoint
    url(r'^apple-app-site-association', AppleAppSiteAssociation.as_view(), name="apple-app-site-association"),

    # JSON-LD Context
    url(r'^json-ld/', include('badgrlog.urls')),

)

if apps.is_installed('issuer'):
    urlpatterns += patterns('',
        url(r'^v1/$', RedirectView.as_view(url='/v1/issuer/issuers', permanent=False)),
        url(r'^v1/issuer', include('issuer.api_urls')),
        url(r'^issuer', include('issuer.urls')),
    )

if apps.is_installed('pathway'):
    urlpatterns += patterns('',
        url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/pathways', include('pathway.api_urls')),
        url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/recipient-groups', include('recipient.api_urls')),
    )

if apps.is_installed('composition'):
    urlpatterns += patterns('',
        url(r'^v1/earner', include('composition.api_urls')),
        url(r'^earner', include('composition.urls')),
    )

if apps.is_installed('badgebook'):
    urlpatterns += patterns('',
        url(r'^v1/badgebook', include('badgebook.api_urls')),
        url(r'^badgebook', include('badgebook.urls')),
    )


handler404 = 'mainsite.views.error404'
handler500 = 'mainsite.views.error500'
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
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
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

# Serve pattern library view only in debug mode or if explicitly declared
if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = patterns('',
       url(r'^component-library$', TemplateView.as_view(template_name='component-library.html'), name='component-library')
    ) + urlpatterns
