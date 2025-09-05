from django.apps import apps
from django.conf import settings
from django.urls import include, path, re_path
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
    SpectacularSwaggerOauthRedirectView,
)
from graphene_django.debug.middleware import DjangoDebugMiddleware

from mainsite.admin import badgr_admin
from mainsite.graphql_view import ExtendedGraphQLView, DisableIntrospectionMiddleware
from mainsite.views import serve_protected_document

badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

from django.views.generic.base import RedirectView, TemplateView

from mainsite.views import SitewideActionFormView
from mainsite.views import email_unsubscribe, error404, error500

urlpatterns = [
    path(
        'graphql',
        csrf_exempt(
            ExtendedGraphQLView.as_view(
                graphiql=True, middleware=[DisableIntrospectionMiddleware(), DjangoDebugMiddleware()]
            )
        ),
    ),
    # Backup URLs in case the server isn't serving these directly
    re_path(
        r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)
    ),
    re_path(
        r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)
    ),
    re_path(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL, permanent=True)),
    # legacy logo url redirect
    re_path(
        r'^static/images/header-logo-120.png$',
        RedirectView.as_view(url='{}images/logo.png'.format(settings.STATIC_URL), permanent=True),
    ),
    # Home
    path('', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),
    # Admin URLs
    path('staff/sidewide-actions', SitewideActionFormView.as_view(), name='badgr_admin_sitewide_actions'),
    re_path(r'^staff/', badgr_admin.urls),
    re_path(r'^staff/superlogin', badgr_admin.login, name='badgr_admin_super_login'),
    # legacy superlogin is now a duplicate of /staff/login
    # Service health endpoint
    path('health/', include('health.urls')),
    # unversioned public endpoints
    re_path(
        r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)',
        email_unsubscribe,
        name='unsubscribe',
    ),
    path('public/', include('public.public_api_urls')),
    # legacy share redirects
    path('', include('backpack.share_urls')),
    # REST Framework
    path('account/', include('badgrsocialauth.redirect_urls')),
    # v1 API endpoints
    path('user/', include('badgeuser.api_urls')),
    path('user/', include('badgrsocialauth.v1_api_urls')),
    path('issuer/', include('issuer.api_urls')),
    path('earner/', include('backpack.v1_api_urls')),
    # include LTI endpoints
    path('lti_edu/', include('lti_edu.api_urls')),
    # include Institution endpoints
    path('institution/', include('institution.api_urls')),
    # include direct award endpoints
    path('directaward/', include('directaward.api_urls')),
    # include insights endpoints
    path('insights/', include('insights.api_urls')),
    # include queries endpoints
    path('queries/', include('queries.api_urls')),
    # include mobile_api endpoints
    path('mobile/api/', include('mobile_api.api_urls')),
    # ob3 poc, proxies impierce endpoints
    path('ob3/', include('ob3.api_urls')),
    # include badge_connect endpoints
    path('badge_connect/', include('badge_connect.api_urls')),
    # include endorsement endpoints
    path('endorsement/', include('endorsement.api_urls')),
    # include lti13 endpoints
    path('lti/', include('lti13.urls')),
    # include notifications endpoints
    path('notifications/', include('notifications.api_urls')),
    # include theming endpoints
    path('', include('theming.api_urls')),
    #  include signing endpoints
    path('signing/', include(('signing.api_urls', 'signing'), namespace='signing_apis')),
    # include staff endpoints
    path('staff-membership/', include('staff.api_urls')),
    # Prometheus
    path('', include('django_prometheus.urls')),
]

# Test URLs to allow you to see these pages while DEBUG is True
if getattr(settings, 'DEBUG_ERRORS', False):
    urlpatterns = [
        path('error/404/', error404, name='404'),
        path('error/500/', error500, name='500'),
    ] + urlpatterns

# If DEBUG_MEDIA is set, have django serve anything in MEDIA_ROOT at MEDIA_URL
if getattr(settings, 'DEBUG_MEDIA', True):
    from django.views.static import serve as static_serve

    media_url = getattr(settings, 'HTTP_ORIGIN_MEDIA', '/media/').lstrip('/')
    urlpatterns = [
        re_path(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ] + urlpatterns

# If DEBUG_STATIC is set, have django serve up static files even if DEBUG=False
if getattr(settings, 'DEBUG_STATIC', True):
    from django.contrib.staticfiles.views import serve as staticfiles_serve

    static_url = getattr(settings, 'STATIC_URL', '/static/')
    static_url = static_url.replace(getattr(settings, 'HTTP_ORIGIN_MEDIA', 'http://localhost:8000'), '')
    static_url = static_url.lstrip('/')
    urlpatterns = [
        re_path(
            r'^%s(?P<path>.*)' % (static_url,),
            staticfiles_serve,
            kwargs={
                'insecure': True,
            },
        )
    ] + urlpatterns

# Serve pattern library view only in debug mode or if explicitly declared
if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = [
        path(
            'component-library', TemplateView.as_view(template_name='component-library.html'), name='component-library'
        )
    ] + urlpatterns

# serve django debug toolbar if present
if settings.DEBUG and apps.is_installed('debug_toolbar'):
    try:
        import debug_toolbar

        urlpatterns = urlpatterns + [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass

# protected assertion media files
urlpatterns.insert(
    0,
    re_path(
        r'^media/(?P<path>.*)$',
        serve_protected_document,
        {'document_root': settings.MEDIA_ROOT},
        name='serve_protected_document',
    ),
)

handler404 = error404
handler500 = error500

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path(
        'api/schema/swagger-ui/oauth2-redirect.html', SpectacularSwaggerOauthRedirectView.as_view(), name='redirect-ui'
    ),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
