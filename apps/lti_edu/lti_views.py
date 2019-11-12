from datetime import timedelta

from django.conf import settings
from django.contrib.auth import login, load_backend, logout
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.http import JsonResponse
from django.urls import reverse
from django.utils.datetime_safe import datetime
from django.views import View
from django.views.generic import TemplateView

from badgeuser.authcode import authcode_for_accesstoken
from badgeuser.models import BadgrAccessToken
from badgrsocialauth.utils import set_session_badgr_app, get_session_badgr_app
from lti_edu.models import LtiBadgeUserTennant
from mainsite.models import BadgrApp


class CheckLogin(View):

    def get(self, request,badgr_app_id):

        response = {'loggedin': True, 'auth_token':''}
        if not request.user.is_authenticated():
            response['loggedin'] = False
        elif not request.user.has_edu_id_social_account():
            response['loggedin'] = False
        if request.user.is_authenticated():
            badgr_app = BadgrApp.objects.get(id=badgr_app_id)
            if badgr_app is not None:

                response['auth_token'] = self.get_access_token(badgr_app, request.user)

        return JsonResponse(response)

    def get_access_token(self, badgr_app, user):
        if BadgrAccessToken.objects.filter(user=user, expires__lt=datetime.now()).exists():
            accesstoken = BadgrAccessToken.objects.filter(user=user).order_by('-created').all()[0]
        else:
            accesstoken = BadgrAccessToken.objects.generate_new_token_for_user(
                user,
                application=badgr_app.oauth_application if badgr_app.oauth_application_id else None,
                scope='rw:backpack rw:profile rw:issuer')

        if badgr_app.use_auth_code_exchange:
            authcode = authcode_for_accesstoken(accesstoken)
            return authcode
        else:
            return accesstoken.token




class CheckLoginAdmin(CheckLogin):
    def get(self, request,badgr_app_id):

        response = {'loggedin': True, 'auth_token':''}
        if not request.user.is_authenticated():
            response['loggedin'] = False
        elif not request.user.has_surf_conext_social_account():
            response['loggedin'] = False
        if request.user.is_authenticated():
            badgr_app = BadgrApp.objects.get(id=badgr_app_id)

            if badgr_app is not None:
                response['auth_token'] = self.get_access_token(badgr_app, request.user)
        return JsonResponse(response)


def login_user(request, user):
    """Log in a user without requiring credentials with user object"""

    if not hasattr(user, 'backend'):
        for backend in settings.AUTHENTICATION_BACKENDS:
            if user == load_backend(backend).get_user(user.pk):
                user.backend = backend
                break
    if hasattr(user, 'backend'):

        return login(request, user)


def check_user_changed(request, user):
    lti_user_id = request.session.get('lti_user_id', None)
    lti_roles = request.session.get('lti_roles', None)
    if lti_user_id == request.POST['user_id'] and lti_roles == request.POST['roles']:
        return False
    """Log in a user without requiring credentials with user object"""
    return logout_badgr_user(request, user)


def logout_badgr_user(request, user):
    if request.user.is_authenticated():
        if not hasattr(user, 'backend'):
            for backend in settings.AUTHENTICATION_BACKENDS:
                try:
                    if user == load_backend(backend).get_user(user.pk):
                        user.backend = backend

                        logout(request)
                except:
                    pass
        # if hasattr(user, 'backend'):
        #     return logout(request)
        # return logout(request)
    return False


class LoginLti(TemplateView):
    template_name = "lti/lti_login.html"
    staff = False
    teacher_roles = [
        'urn:lti:instrole:ims/lis/Administrator',
        'urn:lti:sysrole:ims/lis/SysAdmin',
        'urn:lti:sysrole:ims/lis/Creator',
        'urn:lti:sysrole:ims/lis/Administrator',
        'Instructor',
        'urn:lti:role:ims/lis/TeachingAssistant',
        'ContentDeveloper'

    ]

    # @method_decorator(xframe_options_exempt)
    def dispatch(self, *args, **kwargs):
        response = super(LoginLti, self).dispatch(*args, **kwargs)
        response['X-Frame-Options'] = 'ALLOW-FROM {}'.format(kwargs['tenant'].lms_domain)
        return response

    def get_context_data(self, **kwargs):
        context_data = super(LoginLti, self).get_context_data(**kwargs)

        context_data['ltitest'] = 'yes lti test'
        badgr_app = kwargs['tenant'].badgr_app
        context_data['login_url'] = self.get_login_url()
        context_data['login_image'] = self.get_login_image()
        if badgr_app is not None:
            set_session_badgr_app(self.request, badgr_app)
        else:
            print('badgr app is none in lti_view')

            # check login
        try:
            ltibadgetennant = LtiBadgeUserTennant.objects.get(lti_tennant=kwargs['tenant'],
                                                              lti_user_id=self.request.POST['user_id'],
                                                              staff=self.staff)
            login_user(self.request, ltibadgetennant.badge_user)

        except Exception as e:
            pass

        context_data['after_login'] = self.get_after_login(badgr_app)
        context_data['check_login'] = self.get_check_login_url(badgr_app)
        return context_data

    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            # logout_badgr_user(request, request.user)
            check_user_changed(request, request.user)
        post = request.POST
        user_id = post['user_id']
        context_id = post['context_id']
        roles = ''
        if 'roles' in post:
            roles = post['roles']
            for role in roles.split(','):
                if role in self.teacher_roles:
                    self.staff = True
        lti_data = {}
        lti_data['lti_user_id'] = user_id
        lti_data['lti_roles'] = roles
        lti_data['lti_context_id'] = context_id
        lti_data['lti_tenant'] = kwargs['tenant'].client_key.hex
        lti_data['post_data'] = post
        request.session['lti_data'] = lti_data
        return self.get(request, *args, **kwargs)

    def get_login_url(self):
        if self.staff:
            return self.get_login_url_staff()
        return "{}?provider=edu_id".format(reverse('socialaccount_login'))

    def get_after_login(self, badgr_app):
        if self.staff:
            return self.get_after_login_staff(badgr_app)
        scheme = self.request.is_secure() and "https" or "http"
        return '{}://{}/auth/login?embedVersion=1&embedWidth=800&embedHeight=800&lti_student=true'.format(scheme, badgr_app.cors)

    def get_check_login_url(self, badgr_app):
        if self.staff:
            return self.get_check_login_url_staff(badgr_app)
        return reverse('check-login', kwargs={'badgr_app_id':badgr_app.id})

    def get_login_url_staff(self):
        return "{}?provider=surf_conext".format(reverse('socialaccount_login'))

    def get_after_login_staff(self, badgr_app):
        scheme = self.request.is_secure() and "https" or "http"
        return '{}://{}/auth/login?embedVersion=1&embedWidth=800&embedHeight=800&lti_staff=true'.format(scheme, badgr_app.cors)

    def get_check_login_url_staff(self,badgr_app):
        return reverse('check-login-staff', kwargs={'badgr_app_id':badgr_app.id})

    def get_login_image(self):
        if self.staff:
            return static('images/surf_conext_logo.png')
        return static('images/edu_id_logo.png')




class LoginLtiStaff(LoginLti):
    staff = True

    def get_login_url(self):
        return reverse('surf_conext_login')

    def get_after_login(self, badgr_app):
        scheme = self.request.is_secure() and "https" or "http"
        return '{}://{}/lti-badges/staff?embedVersion=1&embedWidth=800&embedHeight=800'.format(scheme, badgr_app.cors)

    def get_check_login_url(self):
        return reverse('check-login-staff')

    def get_login_image(self):
        return static('images/surf_conext_logo.png')
