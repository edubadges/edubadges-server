from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url

from mainsite.admin import badgr_admin

badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

from django.views.generic.base import RedirectView, TemplateView

from composition.views import LegacyCollectionShareRedirectView
from mainsite.views import info_view, email_unsubscribe, AppleAppSiteAssociation, LoginAndObtainAuthToken, \
    ClearCacheView

urlpatterns = [
    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL)),

    # Apple app universal URL endpoint
    url(r'^apple-app-site-association', AppleAppSiteAssociation.as_view(), name="apple-app-site-association"),

    # Home
    url(r'^$', info_view, name='index'),

    # Admin URLs
    url(r'^staff/clear-cache$', ClearCacheView.as_view(), name='badgr_admin_clear_cache'),
    url(r'^staff/', include(badgr_admin.urls)),

    # Service health endpoint
    url(r'^health', include('health.urls')),

    # Swagger Docs
    url(r'^docs/', include('rest_framework_swagger.urls')),

    # JSON-LD Context
    url(r'^json-ld/', include('badgrlog.urls')),

    # unversioned public endpoints
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe, name='unsubscribe'),

    url(r'^public', include('issuer.public_api_urls')),
    url(r'^public', include('pathway.public_api_urls')),

    url(r'^share', include('composition.share_urls')),
    # legacy share redirects
    url(r'^earner/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection'),
    url(r'^earner/collections/(?P<pk>[^/]+)/(?P<share_hash>[^/]+)/embed$', LegacyCollectionShareRedirectView.as_view(), name='legacy_shared_collection_embed'),

    # REST Framework
    url(r'^api-auth/token$', LoginAndObtainAuthToken.as_view()),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'public/login.html'}, name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': 'login'}, name='logout'),

    # v1 API endpoints
    url(r'^v1/user', include('badgeuser.api_urls')),
    url(r'^v1/issuer', include('issuer.api_urls')),
    url(r'^v1/earner', include('composition.api_urls')),

    # v2 API endpoints
    url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/pathways', include('pathway.api_urls')),
    url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/recipient-groups', include('recipient.api_urls')),

]

if apps.is_installed('badgebook'):
    urlpatterns += [
        url(r'^v1/badgebook', include('badgebook.api_urls')),
        url(r'^badgebook', include('badgebook.urls')),
    ]

# Test URLs to allow you to see these pages while DEBUG is True
if getattr(settings, 'DEBUG_ERRORS', False):
    urlpatterns = [
        url(r'^error/404/$', 'mainsite.views.error404', name='404'),
        url(r'^error/500/$', 'mainsite.views.error500', name='500'),
    ] + urlpatterns

# If DEBUG_MEDIA is set, have django serve anything in MEDIA_ROOT at MEDIA_URL
if getattr(settings, 'DEBUG_MEDIA', True):
    media_url = getattr(settings, 'MEDIA_URL', '/media/').lstrip('/')
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {
            'document_root': settings.MEDIA_ROOT
        }),
    ] + urlpatterns

# If DEBUG_STATIC is set, have django serve up static files even if DEBUG=False
if getattr(settings, 'DEBUG_STATIC', True):
    static_url = getattr(settings, 'STATIC_URL', '/static/').replace(getattr(settings, 'HTTP_ORIGIN', ''), '').lstrip('/')
    urlpatterns = [
        url(r'^%s(?P<path>.*)' % (static_url,), 'django.contrib.staticfiles.views.serve', kwargs={
            'insecure': True,
        })
    ] + urlpatterns

# Serve pattern library view only in debug mode or if explicitly declared
if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = [
       url(r'^component-library$', TemplateView.as_view(template_name='component-library.html'), name='component-library')
    ] + urlpatterns
