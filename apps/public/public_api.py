import io
import os
import re
from urllib.parse import urljoin

import cairosvg
import requests
from PIL import Image
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render
from django.urls import resolve, reverse, Resolver404, NoReverseMatch
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

import badgrlog
from entity.api import VersionedObjectMixin, BaseEntityDetailView
from institution.models import Institution, Faculty
from issuer import utils
from issuer.models import Issuer, BadgeClass, BadgeInstance
from mainsite.exceptions import BadgrApiException400
from mainsite.models import BadgrApp
from mainsite.utils import OriginSetting
from signing.models import PublicKeyIssuer

logger = badgrlog.BadgrLogger()


class AssertionValidate(BaseEntityDetailView):
    """
    Endpoint for validating a badge (GET)
    """

    model = BadgeInstance
    permission_classes = (permissions.AllowAny,)
    http_method_names = ['get']

    def get(self, request, **kwargs):
        assertion = self.get_object(request, **kwargs)
        if assertion.public:
            return Response(assertion.validate(), status=status.HTTP_200_OK)
        else:
            raise Http404


class SlugToEntityIdRedirectMixin(object):
    slugToEntityIdRedirect = False

    def get_entity_id_by_slug(self, slug):
        try:
            object = self.model.cached.get(slug=slug)
            return getattr(object, 'entity_id', None)
        except self.model.DoesNotExist:
            return None

    def get_slug_to_entity_id_redirect_url(self, slug):
        try:
            pattern_name = resolve(self.request.path_info).url_name
            entity_id = self.get_entity_id_by_slug(slug)
            if entity_id is None:
                raise Http404
            return reverse(pattern_name, kwargs={'entity_id': entity_id})
        except (Resolver404, NoReverseMatch):
            return None

    def get_slug_to_entity_id_redirect(self, slug):
        redirect_url = self.get_slug_to_entity_id_redirect_url(slug)
        if redirect_url is not None:
            query = self.request.META.get('QUERY_STRING', '')
            if query:
                redirect_url = '{}?{}'.format(redirect_url, query)
            return redirect(redirect_url, permanent=True)
        else:
            raise Http404


class JSONComponentView(VersionedObjectMixin, APIView, SlugToEntityIdRedirectMixin):
    """
    Abstract Component Class
    """

    permission_classes = (permissions.AllowAny,)
    authentication_classes = ()
    html_renderer_class = None
    template_name = 'public/bot_openbadge.html'

    def log(self, obj):
        pass

    def get_json(self, request, **kwargs):
        json = self.current_object.get_json(obi_version=self._get_request_obi_version(request), **kwargs)
        return json

    def get(self, request, **kwargs):
        try:
            self.current_object = self.get_object(request, **kwargs)
        except Http404:
            if self.slugToEntityIdRedirect:
                return self.get_slug_to_entity_id_redirect(kwargs.get('entity_id', None))
            else:
                raise

        try:
            if not self.current_object.public:
                raise Http404
        except AttributeError:  # object does not have the public attribute
            pass

        self.log(self.current_object)

        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render(request, self.template_name, context=self.get_context_data())

        if self.is_requesting_html():
            return HttpResponseRedirect(redirect_to=self.get_badgrapp_redirect())

        json = self.get_json(request=request)
        return Response(json)

    def is_bot(self):
        """
        bots get an stub that contains opengraph tags
        """
        bot_useragents = getattr(settings, 'BADGR_PUBLIC_BOT_USERAGENTS', ['LinkedInBot'])
        user_agent = self.request.headers.get('user-agent', '')
        if any(a in user_agent for a in bot_useragents):
            return True
        return False

    def is_wide_bot(self):
        """
        some bots prefer a wide aspect ratio for the image
        """
        bot_useragents = getattr(settings, 'BADGR_PUBLIC_BOT_USERAGENTS_WIDE', ['LinkedInBot'])
        user_agent = self.request.headers.get('user-agent', '')
        if any(a in user_agent for a in bot_useragents):
            return True
        return False

    def is_requesting_html(self):
        if self.format_kwarg == 'json':
            return False

        html_accepts = ['text/html']

        http_accept = self.request.headers.get('accept', 'application/json')

        if self.is_bot() or any(a in http_accept for a in html_accepts):
            return True

        return False

    def get_badgrapp_redirect(self):
        badgrapp = self.current_object.cached_badgrapp
        badgrapp = BadgrApp.cached.get(pk=badgrapp.pk)  # ensure we have latest badgrapp information
        if not badgrapp.public_pages_redirect:
            badgrapp = BadgrApp.objects.get_current(request=None)  # use the default badgrapp

        redirect = badgrapp.public_pages_redirect
        if not redirect:
            redirect = 'https://{}/public/'.format(badgrapp.cors)
        else:
            if not redirect.endswith('/'):
                redirect += '/'

        path = self.request.path
        stripped_path = re.sub(r'^/public/', '', path)
        query_string = self.request.META.get('QUERY_STRING', None)
        ret = '{redirect}{path}{query}'.format(
            redirect=redirect, path=stripped_path, query='?' + query_string if query_string else ''
        )
        return ret

    @staticmethod
    def _get_request_obi_version(request):
        return request.query_params.get('v', utils.CURRENT_OBI_VERSION)


class ImagePropertyDetailView(APIView, SlugToEntityIdRedirectMixin):
    permission_classes = (permissions.AllowAny,)

    def get_object(self, entity_id):
        try:
            current_object = self.model.cached.get(entity_id=entity_id)
        except self.model.DoesNotExist:
            return None
        else:
            return current_object

    def get(self, request, **kwargs):
        entity_id = kwargs.get('entity_id')
        current_object = self.get_object(entity_id)
        if current_object is None and self.slugToEntityIdRedirect and getattr(request, 'version', 'v1') == 'v2':
            return self.get_slug_to_entity_id_redirect(kwargs.get('entity_id', None))
        elif current_object is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        image_prop = getattr(current_object, self.prop)
        if not bool(image_prop):
            return Response(status=status.HTTP_404_NOT_FOUND)
        lang = request.query_params.get('lang')
        if lang:
            if lang == 'en' and hasattr(current_object, self.prop_en):
                image_prop = getattr(current_object, self.prop_en)
            if lang == 'nl' and hasattr(current_object, self.prop_nl):
                image_prop = getattr(current_object, self.prop_nl)

        image_type = request.query_params.get('type', 'original')
        if image_type not in ['original', 'png']:
            raise ValidationError('invalid image type: {}'.format(image_type))

        supported_fmts = {'square': (1, 1), 'wide': (1.91, 1)}
        image_fmt = request.query_params.get('fmt', 'square').lower()
        if image_fmt not in list(supported_fmts.keys()):
            raise ValidationError('invalid image format: {}'.format(image_fmt))

        image_url = image_prop.url
        filename, ext = os.path.splitext(image_prop.name)
        basename = os.path.basename(filename)
        dirname = os.path.dirname(filename)
        version_suffix = getattr(settings, 'CAIROSVG_VERSION_SUFFIX', '1')
        new_name = '{dirname}/converted{version}/{basename}{fmt_suffix}.png'.format(
            dirname=dirname,
            basename=basename,
            version=version_suffix,
            fmt_suffix='-{}'.format(image_fmt) if image_fmt != 'square' else '',
        )
        storage = DefaultStorage()

        def _fit_to_height(img, ar, height=400):
            img.thumbnail((height, height))
            new_size = (int(ar[0] * height), int(ar[1] * height))
            new_img = Image.new('RGBA', new_size)
            new_img.paste(img, ((new_size[0] - height) / 2, (new_size[1] - height) / 2))
            new_img.show()
            return new_img

        if image_type == 'original' and image_fmt == 'square':
            image_url = image_prop.url
        elif ext == '.svg':
            if not storage.exists(new_name):
                with storage.open(image_prop.name, 'rb') as input_svg:
                    svg_buf = io.StringIO()
                    out_buf = io.StringIO()
                    cairosvg.svg2png(file_obj=input_svg, write_to=svg_buf)
                    img = Image.open(svg_buf)

                    img = _fit_to_height(img, supported_fmts[image_fmt])

                    img.save(out_buf, format='png')
                    storage.save(new_name, out_buf)
            image_url = storage.url(new_name)
        else:
            if not storage.exists(new_name):
                with storage.open(image_prop.name, 'rb') as input_svg:
                    out_buf = io.StringIO()
                    img = Image.open(input_svg)

                    img = _fit_to_height(img, supported_fmts[image_fmt])

                    img.save(out_buf, format='png')
                    storage.save(new_name, out_buf)
            image_url = storage.url(new_name)

        return redirect(image_url)


class InstitutionJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = Institution

    def get_context_data(self, **kwargs):
        image_url = '{}{}?type=png'.format(
            OriginSetting.HTTP, reverse('institution_image', kwargs={'entity_id': self.current_object.entity_id})
        )
        if self.is_wide_bot():
            image_url = '{}&fmt=wide'.format(image_url)

        return dict(
            title=self.current_object.name,
            image_url=image_url,
        )


class InstitutionImage(ImagePropertyDetailView):
    model = Institution
    prop = 'image'
    prop_en = 'image_english'
    prop_nl = 'image_dutch'

    def log(self, obj):
        logger.event(badgrlog.InstitutionImageRetrievedEvent(obj, self.request))


class FacultyImage(ImagePropertyDetailView):
    model = Faculty
    prop = 'image'
    prop_en = 'image_english'
    prop_nl = 'image_dutch'

    def log(self, obj):
        logger.event(badgrlog.FacultyImageRetrievedEvent(obj, self.request))


class IssuerJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = Issuer

    def log(self, obj):
        logger.event(badgrlog.IssuerRetrievedEvent(obj, self.request))

    def get_json(self, request, **kwargs):
        expands = request.GET.getlist('expand', [])
        json = super(IssuerJson, self).get_json(request)
        obi_version = self._get_request_obi_version(request)

        if 'institution' in expands:
            json['faculty'] = {
                'name': self.current_object.faculty.name,
                'institution': self.current_object.faculty.institution.get_json(obi_version=obi_version),
            }

        return json

    def get_context_data(self, **kwargs):
        image_url = '{}{}?type=png'.format(
            OriginSetting.HTTP, reverse('issuer_image', kwargs={'entity_id': self.current_object.entity_id})
        )
        if self.is_wide_bot():
            image_url = '{}&fmt=wide'.format(image_url)

        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url,
        )


class IssuerPublicKeyJson(IssuerJson):
    def get(self, request, **kwargs):
        self.current_object = self.get_object(request, **kwargs)
        self.log(self.current_object)

        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render(request, self.template_name, context=self.get_context_data())

        pubkey_issuer = PublicKeyIssuer.objects.get(entity_id=kwargs.get('public_key_id'))
        issuer_json = self.get_json(
            request=request, signed=True, public_key_issuer=pubkey_issuer, expand_public_key=False
        )
        return Response(issuer_json)


class IssuerBadgesJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = Issuer

    def log(self, obj):
        logger.event(badgrlog.IssuerBadgesRetrievedEvent(obj, self.request))

    def get_json(self, request):
        obi_version = self._get_request_obi_version(request)

        return [b.get_json(obi_version=obi_version) for b in self.current_object.cached_badgeclasses()]


class IssuerImage(ImagePropertyDetailView):
    model = Issuer
    prop = 'image'
    prop_en = 'image_english'
    prop_nl = 'image_dutch'

    def log(self, obj):
        logger.event(badgrlog.IssuerImageRetrievedEvent(obj, self.request))


class BadgeClassJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = BadgeClass

    def log(self, obj):
        logger.event(badgrlog.BadgeClassRetrievedEvent(obj, self.request))

    def get_json(self, request):
        badge_class = self.current_object
        if badge_class.is_private:
            raise Http404

        expands = request.GET.getlist('expand', [])
        json = super(BadgeClassJson, self).get_json(request)
        obi_version = self._get_request_obi_version(request)
        expand_awards = 'awards' in expands

        if expand_awards:
            json['award_allowed_institutions'] = [inst.name for inst in badge_class.award_allowed_institutions.all()]
            json['formal'] = badge_class.formal
            json['archived'] = badge_class.archived
            json['self_enrollment_disabled'] = badge_class.self_enrollment_disabled
            json['awardNonValidatedNameAllowed'] = badge_class.award_non_validated_name_allowed
        if 'issuer' in expands:
            json['issuer'] = badge_class.cached_issuer.get_json(
                obi_version=obi_version, expand_institution=True, expand_awards=expand_awards
            )
        if 'endorsements' in expands:
            json['endorsements'] = [self.endorsement_to_json(bc) for bc in badge_class.cached_endorsements()]
            json['endorsed'] = [endorsement.endorsee.entity_id for endorsement in badge_class.cached_endorsed()]
        if 'micro' in expands:
            json['participation'] = badge_class.participation
            json['assessmentType'] = badge_class.assessment_type
            json['assessmentIdVerified'] = badge_class.assessment_id_verified
            json['assessmentSupervised'] = badge_class.assessment_supervised
            json['qualityAssuranceDescription'] = badge_class.quality_assurance_description
            json['qualityAssuranceName'] = badge_class.quality_assurance_name
            json['qualityAssuranceUrl'] = badge_class.quality_assurance_url
            json['participation'] = badge_class.participation
            json['stackable'] = badge_class.stackable
            json['gradeAchievedRequired'] = badge_class.grade_achieved_required
            json['eqfNlqfLevelVerified'] = badge_class.eqf_nlqf_level_verified
            json['typeBadgeClass'] = badge_class.badge_class_type
        return json

    @staticmethod
    def _image_urls(obj, name, container):
        image_url = OriginSetting.HTTP + reverse(f'{name}_image', kwargs={'entity_id': obj.entity_id})
        if hasattr(obj, 'image'):
            container['image'] = image_url
        if hasattr(obj, 'image_english') and obj.image_english:
            container['imageEnglish'] = f'{image_url}?lang=en'
        if hasattr(obj, 'imageDutch') and obj.image_dutch:
            container['image_dutch'] = f'{image_url}?lang=nl'

    @staticmethod
    def endorsement_to_json(endorsement):
        endorser = endorsement.endorser
        issuer = endorser.cached_issuer
        faculty = issuer.faculty
        institution = faculty.institution
        to_json = {
            'claim': endorsement.claim,
            'description': endorsement.description,
            'status': endorsement.status,
            'endorser': {
                'name': endorser.name,
                'description': endorser.description,
                'entityId': endorser.entity_id,
                'issuer': {
                    'nameDutch': issuer.name_dutch,
                    'nameEnglish': issuer.name_english,
                    'entityId': issuer.entity_id,
                    'faculty': {
                        'nameDutch': faculty.name_dutch,
                        'nameEnglish': faculty.name_english,
                        'onBehalfOf': faculty.on_behalf_of,
                        'onBehalfOfUrl': faculty.on_behalf_of_url,
                        'onBehalfOfDisplayName': faculty.on_behalf_of_display_name,
                        'entityId': faculty.entity_id,
                        'institution': {
                            'nameDutch': institution.name_dutch,
                            'nameEnglish': institution.name_english,
                            'entityId': institution.entity_id,
                        },
                    },
                },
            },
        }
        BadgeClassJson._image_urls(issuer, 'issuer', to_json['endorser']['issuer'])
        BadgeClassJson._image_urls(institution, 'institution', to_json['endorser']['issuer']['faculty']['institution'])
        BadgeClassJson._image_urls(endorser, 'badgeclass', to_json['endorser'])
        return to_json

    def get_context_data(self, **kwargs):
        image_url = '{}{}?type=png'.format(
            OriginSetting.HTTP, reverse('badgeclass_image', kwargs={'entity_id': self.current_object.entity_id})
        )
        if self.is_wide_bot():
            image_url = '{}&fmt=wide'.format(image_url)
        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url,
        )


class BadgeClassPublicKeyJson(BadgeClassJson):
    def get(self, request, **kwargs):
        self.current_object = self.get_object(request, **kwargs)
        self.log(self.current_object)
        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render(request, self.template_name, context=self.get_context_data())

        public_key_issuer = PublicKeyIssuer.objects.get(entity_id=kwargs.get('public_key_id'))
        json = self.current_object.get_json(signed=True, public_key_issuer=public_key_issuer)
        return Response(json)


class BadgeClassImage(ImagePropertyDetailView):
    model = BadgeClass
    prop = 'image'

    def log(self, obj):
        logger.event(badgrlog.BadgeClassImageRetrievedEvent(obj, self.request))


class BadgeClassCriteria(RedirectView, SlugToEntityIdRedirectMixin):
    permanent = False
    model = BadgeClass

    def get_redirect_url(self, *args, **kwargs):
        try:
            badge_class = self.model.cached.get(entity_id=kwargs.get('entity_id'))
        except self.model.DoesNotExist:
            if self.slugToEntityIdRedirect:
                return self.get_slug_to_entity_id_redirect_url(kwargs.get('entity_id'))
            else:
                return None
        return badge_class.get_absolute_url()


class BadgeInstanceJson(JSONComponentView):
    """
    ## You might see this screen because the badge you are looking for is <span style="color:red">*set to private*</span>.
    ## Ask the recipient to set the badge to public, then try again.
    """

    permission_classes = (permissions.AllowAny,)
    model = BadgeInstance

    def get_json(self, request):
        if self.object.signature:
            json = self.object.signature  # return signature in stead of json for signed badges
        else:
            expands = request.GET.getlist('expand', [])
            json = super(BadgeInstanceJson, self).get_json(
                request,
                expand_badgeclass=('badge' in expands),
                expand_issuer=('badge.issuer' in expands),
                expand_user=('badge.user' in expands),
            )
        return json

    def get_context_data(self, **kwargs):
        image_url = '{}{}?type=png'.format(
            OriginSetting.HTTP,
            reverse('badgeclass_image', kwargs={'entity_id': self.current_object.cached_badgeclass.entity_id}),
        )
        if self.is_wide_bot():
            image_url = '{}&fmt=wide'.format(image_url)
        return dict(
            title=self.current_object.cached_badgeclass.name,
            description=self.current_object.cached_badgeclass.description,
            public_url=self.current_object.public_url,
            image_url=image_url,
        )


class BadgeInstanceImage(ImagePropertyDetailView):
    model = BadgeInstance
    prop = 'image'

    def log(self, badge_instance):
        logger.event(badgrlog.BadgeInstanceDownloadedEvent(badge_instance, self.request))

    def get_object(self, slug):
        obj = super(BadgeInstanceImage, self).get_object(slug)
        if obj and obj.revoked:
            return None
        return obj


class BakedBadgeInstanceImage(VersionedObjectMixin, APIView, SlugToEntityIdRedirectMixin):
    permission_classes = (permissions.AllowAny,)
    model = BadgeInstance

    def get(self, request, **kwargs):
        try:
            assertion = self.get_object(request, **kwargs)
        except Http404:
            if self.slugToEntityIdRedirect:
                return self.get_slug_to_entity_id_redirect(kwargs.get('entity_id', None))
            else:
                raise

        requested_version = request.query_params.get('v', utils.CURRENT_OBI_VERSION)
        if requested_version not in list(utils.OBI_VERSION_CONTEXT_IRIS.keys()):
            raise ValidationError('Invalid OpenBadges version')

        # self.log(assertion)

        redirect_url = assertion.get_baked_image_url(obi_version=requested_version)

        return redirect(redirect_url, permanent=True)


class AssertionRecipientName(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ('get',)

    def get(self, request, *args, **kwargs):
        identity = kwargs.get('identity', None)
        salt = kwargs.get('salt', None)
        if not identity or not salt:
            raise BadgrApiException400('Cannot query name: salt and identity needed', 0)
        instance = BadgeInstance.objects.get(salt=salt)
        if instance.public:
            if identity == instance.get_hashed_identity():
                return Response({'name': instance.get_recipient_name()})
        return Response(status=status.HTTP_404_NOT_FOUND)


class ValidatorVersion(APIView):
    permission_classes = (permissions.AllowAny,)
    http_method_names = ('get',)

    @method_decorator(never_cache)
    def get(self, request, *args, **kwargs):
        response = requests.get(headers={'Accept': 'application/json'}, url=urljoin(settings.VALIDATOR_URL, 'git.info'))
        return Response(response.json(), status=status.HTTP_200_OK)
