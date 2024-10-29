from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.base import RedirectView, TemplateView
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerOauthRedirectView,
    SpectacularSwaggerView,
)
from graphene_django.debug.middleware import DjangoDebugMiddleware

from mainsite.admin import badgr_admin
from mainsite.graphql_view import DisableIntrospectionMiddleware, ExtendedGraphQLView
from mainsite.views import SitewideActionFormView, email_unsubscribe, error404, error500
from mainsite.views import serve_protected_document

badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

urlpatterns = [
    path("graphql", csrf_exempt(ExtendedGraphQLView.as_view(
        graphiql=True, middleware=[DisableIntrospectionMiddleware(), DjangoDebugMiddleware()]))),

    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL, permanent=True)),

    # legacy logo url redirect
    url(r'^static/images/header-logo-120.png$',
        RedirectView.as_view(url='{}images/logo.png'.format(settings.STATIC_URL), permanent=True)),

    # Home
    url(r'^$', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=True)),

    # Admin URLs
    url(r'^staff/sidewide-actions$', SitewideActionFormView.as_view(), name='badgr_admin_sitewide_actions'),
    url(r'^staff/', badgr_admin.urls),
    url(r'^staff/superlogin', badgr_admin.login, name='badgr_admin_super_login'),
    # legacy superlogin is now a duplicate of /staff/login

    # Service health endpoint
    url(r'^health', include('health.urls')),

    # unversioned public endpoints
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe,
        name='unsubscribe'),

    url(r'^public/', include('public.public_api_urls')),

    # legacy share redirects
    url(r'', include('backpack.share_urls')),

    # REST Framework
    url(r'^account/', include('badgrsocialauth.redirect_urls')),

    # v1 API endpoints
    url(r'^user/', include('badgeuser.api_urls')),
    url(r'^user/', include('badgrsocialauth.v1_api_urls')),

    url(r'^issuer/', include('issuer.api_urls')),
    url(r'^earner/', include('backpack.v1_api_urls')),

    # include LTI endpoints
    url(r'^lti_edu/', include('lti_edu.api_urls')),

    # include Institution endpoints
    url(r'^institution/', include('institution.api_urls')),

    # include direct award endpoints
    url(r'^directaward/', include('directaward.api_urls')),

    # include insights endpoints
    url(r'^insights/', include('insights.api_urls')),

    # ob3 poc, proxies impierce endpoints
    url(r'^ob3/', include('ob3.api_urls')),

    # include badge_connect endpoints
    url(r'^badge_connect/', include('badge_connect.api_urls')),

    # include endorsement endpoints
    url(r'^endorsement/', include('endorsement.api_urls')),

    # include lti13 endpoints
    url(r'^lti/', include('lti13.urls')),

    # include notifications endpoints
    url(r'^notifications/', include('notifications.api_urls')),

    # include theming endpoints
    url(r'', include('theming.api_urls')),

    #  include signing endpoints
    url(r'^signing/', include(('signing.api_urls', 'signing'), namespace='signing_apis')),

    # include staff endpoints
    url(r'^staff-membership/', include('staff.api_urls')),

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

    media_url = getattr(settings, 'HTTP_ORIGIN_MEDIA', '/media/').lstrip('/')
    urlpatterns = [
                      url(r'^media/(?P<path>.*)$', static_serve, {
                          'document_root': settings.MEDIA_ROOT
                      }),
                  ] + urlpatterns

# If DEBUG_STATIC is set, have django serve up static files even if DEBUG=False
if getattr(settings, 'DEBUG_STATIC', True):
    from django.contrib.staticfiles.views import serve as staticfiles_serve

    static_url = getattr(settings, 'STATIC_URL', '/static/')
    static_url = static_url.replace(getattr(settings, 'HTTP_ORIGIN_MEDIA', 'http://localhost:8000'), '')
    static_url = static_url.lstrip('/')
    urlpatterns = [
                      url(r'^%s(?P<path>.*)' % (static_url,), staticfiles_serve, kwargs={
                          'insecure': True,
                      })
                  ] + urlpatterns

# Serve pattern library view only in debug mode or if explicitly declared
if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = [
                      url(r'^component-library$', TemplateView.as_view(template_name='component-library.html'),
                          name='component-library')
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

# protected assertion media files
urlpatterns.insert(0,
                   url(r'^media/(?P<path>.*)$', serve_protected_document, {'document_root': settings.MEDIA_ROOT},
                       name='serve_protected_document'),
                   )

handler404 = error404
handler500 = error500

urlpatterns += [
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/schema/swagger-ui/oauth2-redirect.html', SpectacularSwaggerOauthRedirectView.as_view(),
         name='redirect-ui'),
    path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
