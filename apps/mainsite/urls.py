from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url
from rest_framework.authtoken.views import obtain_auth_token

from mainsite.admin import badgr_admin

badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

from django.views.generic.base import RedirectView, TemplateView

from composition.views import LegacyCollectionShareRedirectView
from mainsite.views import ClearCacheView
from mainsite.views import info_view, email_unsubscribe, AppleAppSiteAssociation, error404, error500
from django.contrib.auth import views as contrib_auth_views


urlpatterns = [
    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL, permanent=True)),

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
    # url(r'^docs/', include('rest_framework_swagger.urls')),

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
    url(r'^api-auth/token$', obtain_auth_token),
    url(r'^accounts/login/$', contrib_auth_views.login, {'template_name': 'public/login.html'}, name='login'),
    url(r'^accounts/logout/$', contrib_auth_views.logout, {'next_page': 'login'}, name='logout'),

    # v1 API endpoints
    url(r'^(?P<version>v1)/issuer/', include('issuer.v1_api_urls')),
    url(r'^(?P<version>v1)/user/', include('badgeuser.v1_api_urls')),
    url(r'^v1/earner', include('composition.api_urls')),

    # v2 API endpoints
    url(r'^(?P<version>v2)/', include('issuer.v2_api_urls')),
    url(r'^(?P<version>v2)/', include('badgeuser.v2_api_urls')),


    url(r'^v1/issuers/(?P<issuer_slug>[^/]+)/pathways', include('pathway.api_urls')),
    url(r'^v1/issuers/(?P<issuer_slug>[^/]+)/recipient-groups', include('recipient.api_urls')),

]

if apps.is_installed('badgebook'):
    urlpatterns += [
        url(r'^v1/badgebook', include('badgebook.api_urls')),
        url(r'^badgebook', include('badgebook.urls')),
    ]

# Test URLs to allow you to see these pages while DEBUG is True
if getattr(settings, 'DEBUG_ERRORS', False):
    urlpatterns = [
        url(r'^error/404/$', error404, name='404'),
        url(r'^error/500/$', error500, name='500'),
    ] + urlpatterns

# If DEBUG_MEDIA is set, have django serve anything in MEDIA_ROOT at MEDIA_URL
if getattr(settings, 'DEBUG_MEDIA', True):
    from django.views.static import serve as static_serve
    media_url = getattr(settings, 'MEDIA_URL', '/media/').lstrip('/')
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', static_serve, {
            'document_root': settings.MEDIA_ROOT
        }),
    ] + urlpatterns

# If DEBUG_STATIC is set, have django serve up static files even if DEBUG=False
if getattr(settings, 'DEBUG_STATIC', True):
    from django.contrib.staticfiles.views import serve as staticfiles_serve
    static_url = getattr(settings, 'STATIC_URL', '/static/')
    static_url = static_url.replace(getattr(settings, 'HTTP_ORIGIN', 'http://localhost:8000'), '')
    static_url = static_url.lstrip('/')
    urlpatterns = [
        url(r'^%s(?P<path>.*)' % (static_url,), staticfiles_serve, kwargs={
            'insecure': True,
        })
    ] + urlpatterns

# Serve pattern library view only in debug mode or if explicitly declared
if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = [
       url(r'^component-library$', TemplateView.as_view(template_name='component-library.html'), name='component-library')
    ] + urlpatterns

# serve django debug toolbar if present
if settings.DEBUG and apps.is_installed('debug_toolbar'):
    try:
        import debug_toolbar
        urlpatterns = urlpatterns + [
            url(r'^__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
