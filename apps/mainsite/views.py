import base64
import json
import time
import os

from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.template import loader, TemplateDoesNotExist
from django.urls import reverse_lazy
from django.utils import translation
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import FormView, RedirectView, TemplateView
from django.views.static import serve
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from badgrsocialauth.utils import get_privacy_content
from issuer.tasks import rebake_all_assertions, update_issuedon_all_assertions
from issuer.models import BadgeInstance
from mainsite.admin_actions import clear_cache
from mainsite.models import EmailBlacklist, BadgrApp



##
#
#  Error Handler Views
#
##


@xframe_options_exempt
def error404(request, exception):
    try:
        template = loader.get_template('error/404.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Page not found (404)</h1>', content_type='text/html')
    return HttpResponseNotFound(template.render({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    }))


@xframe_options_exempt
def error500(request):
    try:
        template = loader.get_template('error/500.html')
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    return HttpResponseServerError(template.render({
        'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
    }))


def info_view(request):
    return redirect(getattr(settings, 'LOGIN_REDIRECT_URL'))


def email_unsubscribe(request, *args, **kwargs):
    if time.time() > int(kwargs['expiration']):
        return HttpResponse('Your unsubscription link has expired.')

    try:
        email = base64.b64decode(kwargs['email_encoded'])
    except TypeError:
        return HttpResponse('Invalid unsubscribe link.')

    if not EmailBlacklist.verify_email_signature(**kwargs):
        return HttpResponse('Invalid unsubscribe link.')

    blacklist_instance = EmailBlacklist(email=email)
    try:
        blacklist_instance.save()
    except IntegrityError:
        pass

    return HttpResponse("You will no longer receive email notifications for \
                        earned badges from this domain.")


class AppleAppSiteAssociation(APIView):
    renderer_classes = (JSONRenderer,)
    permission_classes = (AllowAny,)

    def get(self, request):
        data = {
            "applinks": {
                "apps": [],
                "details": []
            }
        }

        for app_id in getattr(settings, 'APPLE_APP_IDS', []):
            data['applinks']['details'].append(app_id)

        return Response(data=data)


class SitewideActionForm(forms.Form):
    ACTION_CLEAR_CACHE = 'CLEAR_CACHE'
    ACTION_RESAVE_ELEMENTS = 'RESAVE_ELEMENTS'
    ACTION_REBAKE_ALL_ASSERTIONS = "REBAKE_ALL_ASSERTIONS"
    ACTION_FIX_ISSUEDON = 'FIX_ISSUEDON'

    ACTIONS = {
        ACTION_CLEAR_CACHE: clear_cache,
        ACTION_REBAKE_ALL_ASSERTIONS: rebake_all_assertions,
        ACTION_FIX_ISSUEDON: update_issuedon_all_assertions,
    }
    CHOICES = (
        (ACTION_CLEAR_CACHE, 'Clear Cache',),
        (ACTION_RESAVE_ELEMENTS, 'Re-save Pathway Elements',),
        (ACTION_REBAKE_ALL_ASSERTIONS, 'Rebake all assertions',),
        (ACTION_FIX_ISSUEDON, 'Re-process issuedOn for backpack assertions',),
    )

    action = forms.ChoiceField(choices=CHOICES, required=True, label="Pick an action")
    confirmed = forms.BooleanField(required=True, label='Are you sure you want to perform this action?')


class SitewideActionFormView(FormView):
    form_class = SitewideActionForm
    template_name = 'admin/sitewide_actions.html'
    success_url = reverse_lazy('admin:index')
    
    def render_to_response(self, context, **response_kwargs):
        if self.request.user.is_superuser:
            return super(SitewideActionFormView, self).render_to_response(context, **response_kwargs)
        else:
            return HttpResponseForbidden()
        
    @method_decorator(staff_member_required)
    def dispatch(self, request, *args, **kwargs):
        return super(SitewideActionFormView, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        action = form.ACTIONS[form.cleaned_data['action']]

        if hasattr(action, 'delay'):
            action.delay()
        else:
            action()

        return super(SitewideActionFormView, self).form_valid(form)


class DocsAuthorizeRedirect(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        badgrapp = BadgrApp.objects.get_current(request=self.request)
        url = badgrapp.oauth_authorization_redirect
        if not url:
            url = 'https://{cors}/auth/oauth2/authorize'.format(cors=badgrapp.cors)

        query = self.request.META.get('QUERY_STRING', '')
        if query:
            url = "{}?{}".format(url, query)
        return url


class TermsAndConditionsView(TemplateView):
    
    template_name = 'terms_of_service/accept_terms_versioned.html'
    
    def get_context_data(self, **kwargs):
        context = super(TermsAndConditionsView, self).get_context_data(**kwargs)
        badgr_app_pk = json.loads(kwargs['state'])[0]
        badgr_app = BadgrApp.objects.get(pk=badgr_app_pk)
        login_type = json.loads(kwargs['state'])[1]
        context['home_url'] = badgr_app.ui_login_redirect
        context['dutch_url'] = '{}?lang=nl'.format(self.request.build_absolute_uri('?'))
        context['english_url'] = '{}?lang=en'.format(self.request.build_absolute_uri('?'))

        lang_code = translation.get_language().lower()
        lang_get = self.request.GET.get('lang', None)
        if lang_get != 'en' and \
                (lang_code in ['nl-nl', 'nl-be', 'nl'] or
                 lang_get == 'nl'):
            context['privacy_content'] = get_privacy_content('create_account_student_nl')
            if login_type == 'surf_conext':
                context['privacy_content'] = get_privacy_content('create_account_employee_nl')
            context['other_lang_url'] = '{}?lang=en'.format(self.request.build_absolute_uri('?'))
            context['other_lang'] = 'Go to english version'
            context['consent_button'] = 'IK GEEF TOESTEMMING'
            context['no_consent_button'] = 'IK GEEF GEEN TOESTEMMING'
            context['resign_text'] = "De algemene voorwaarden zijn veranderd en dienen opnieuw getekend te worden"
        else:
            context['privacy_content'] = get_privacy_content('create_account_student_en')
            if login_type == 'surf_conext':
                context['privacy_content'] = get_privacy_content('create_account_employee_en')
            context['other_lang_url'] = '{}?lang=nl'.format(self.request.build_absolute_uri('?'))
            context['other_lang'] = 'Ga naar nederlands versie'
            context['consent_button'] = 'I CONSENT'
            context['no_consent_button'] = 'I DO NOT CONSENT'
            context['resign_text'] = "The terms and conditions have changed please resign"

        context['privacy_statement_url'] = badgr_app.public_pages_redirect + '/privacy-policy'
        if login_type == 'surf_conext':
            context['ui_login_redirect'] = badgr_app.ui_login_redirect.replace('login', 'staff-login')
        elif login_type == 'edu_id':
            context['ui_login_redirect'] = badgr_app.ui_login_redirect
        return context


class TermsAndConditionsResignView(TermsAndConditionsView):
    template_name = 'terms_of_service/accept_terms_resign.html'


class AcceptTermsAndConditionsView(View):

    def post(self, request, **kwargs):
        pass

    def get(self, request, **kwargs):
        pass


def serve_protected_document(request, path, document_root):
    if 'assertion-' in path:
        assertion = BadgeInstance.objects.get(image=path)
        if assertion.public:
            return serve(request, path, document_root)
        else:
            if request.user.is_authenticated:
                if request.user is assertion.user or request.user.get_permissions(assertion)['may_read']:
                    return serve(request, path, document_root)
        return HttpResponseForbidden()
    return serve(request, path, document_root)
