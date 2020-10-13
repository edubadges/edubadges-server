from django.apps import apps
from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import csrf_exempt
from django.urls import path

from ims.views import base
from mainsite.admin import badgr_admin
from mainsite.graphql_view import ExtendedGraphQLView
from mainsite.views import serve_protected_document

badgr_admin.autodiscover()
# make sure that any view/model/form imports occur AFTER admin.autodiscover

from django.views.generic.base import RedirectView, TemplateView

from mainsite.views import SitewideActionFormView, DocsAuthorizeRedirect, \
    TermsAndConditionsView, TermsAndConditionsResignView, AcceptTermsAndConditionsView
from mainsite.views import info_view, email_unsubscribe, error404, error500


urlpatterns = [
    path("graphql", csrf_exempt(ExtendedGraphQLView.as_view(graphiql=True))),

    # Backup URLs in case the server isn't serving these directly
    url(r'^favicon\.png[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^favicon\.ico[/]?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL, permanent=True)),

    # legacy logo url redirect
    url(r'^static/images/header-logo-120.png$', RedirectView.as_view(url='{}images/logo.png'.format(settings.STATIC_URL), permanent=True)),

    # Home
    url(r'^$', info_view, name='index'),

    # Admin URLs
    url(r'^staff/sidewide-actions$', SitewideActionFormView.as_view(), name='badgr_admin_sitewide_actions'),
    url(r'^staff/', badgr_admin.urls),
    url(r'^staff/superlogin', badgr_admin.login, name='badgr_admin_super_login'),  # legacy superlogin is now a duplicate of /staff/login

    # Service health endpoint
    url(r'^health', include('health.urls')),

    # api docs
    url(r'^docs/oauth2/authorize$', DocsAuthorizeRedirect.as_view(), name='docs_authorize_redirect'),
    url(r'^docs/?$', RedirectView.as_view(url='/docs/v2/', permanent=True)),  # default redirect to /v2/
    url(r'^docs/', include('apispec_drf.urls')),

    # unversioned public endpoints
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe, name='unsubscribe'),

    url(r'^public/', include('issuer.public_api_urls'), kwargs={'version': 'v2'}),

    # legacy share redirects
    url(r'', include('backpack.share_urls')),

    # REST Framework
    url(r'^account/', include('badgrsocialauth.redirect_urls')),

    # v1 API endpoints
    url(r'^v1/user/', include('badgeuser.api_urls'), kwargs={'version': 'v1'}),
    url(r'^v1/user/', include('badgrsocialauth.v1_api_urls'), kwargs={'version': 'v1'}),

    url(r'^issuer/', include('issuer.api_urls'), kwargs={'version': 'v1'}),
    url(r'^v1/earner/', include('backpack.v1_api_urls'), kwargs={'version': 'v1'}),

    # include LTI endpoints
    url(r'^lti_edu/', include('lti_edu.api_urls')),

    # # include Institution endpoints
    url(r'^institution/', include('institution.api_urls')),

    url(r'^lti_issuer/', include('lti_edu.lti_urls')),


    # include theming endpoints
    url(r'v1/', include('theming.api_urls'), kwargs={'version': 'v1'}),

    # Accept Terms View - TODO remove them as the client now renders them
    url(r'^accept_terms/(?P<after_terms_agreement_url_name>[^/]+)/(?P<state>[^/]+)/(?P<id_token>[^/]+)', TermsAndConditionsView.as_view(), name='accept_terms'),
    url(r'^accept_terms_resign/(?P<after_terms_agreement_url_name>[^/]+)/(?P<state>[^/]+)/(?P<id_token>[^/]+)', TermsAndConditionsResignView.as_view(), name='accept_terms_resign'),
    url(r'^accept_terms_resign_accepted/(?P<after_terms_agreement_url_name>[^/]+)/(?P<state>[^/]+)/(?P<id_token>[^/]+)', AcceptTermsAndConditionsView.as_view(), name='accept_terms_resign_accepted'),

    #  include signing endpoints
    url(r'^signing/', include('signing.api_urls')),

    # include staff endpoints
    url(r'^staff-membership/', include('staff.api_urls')),

]

urlpatterns += [
    url(
        r'^lti_app/(?P<app_slug>[A-Za-z0-9\-]+)/config/(?P<tenant_slug>[A-Za-z0-9\-]+)\.xml$',
        base.lti_config,
        name='lti-config'
    ),
    url(r'^lti_app/(?P<slug>[A-Za-z0-9\-]+)/?$', base.lti_launch)
]

urlpatterns += [
    url(
        r'^lti_app/(?P<app_slug>[A-Za-z0-9\-]+)/config/(?P<tenant_slug>[A-Za-z0-9\-]+)\.xml$',
        base.lti_config,
        name='lti-config'
    ),
    url(r'^lti_app/(?P<slug>[A-Za-z0-9\-]+)/?$', base.lti_launch)
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


# protected assertion media files
urlpatterns.insert(0,
    url(r'^media/(?P<path>.*)$', serve_protected_document, {'document_root': settings.MEDIA_ROOT}, name='serve_protected_document'),
)

handler404 = error404
handler500 = error500
