import io
import os
import re

import badgrlog
import cairosvg
from PIL import Image
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.urls import resolve, reverse, Resolver404, NoReverseMatch
from django.views.generic import RedirectView
from entity.api import VersionedObjectMixin
from mainsite.models import BadgrApp
from mainsite.utils import OriginSetting
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView
from signing.models import PublicKeyIssuer

from . import utils
from .models import Issuer, BadgeClass, BadgeInstance

logger = badgrlog.BadgrLogger()


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
                redirect_url = "{}?{}".format(redirect_url, query)
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
            return render_to_response(self.template_name, context=self.get_context_data())

        if self.is_requesting_html():
            return HttpResponseRedirect(redirect_to=self.get_badgrapp_redirect())

        json = self.get_json(request=request)
        return Response(json)

    def is_bot(self):
        """
        bots get an stub that contains opengraph tags
        """
        bot_useragents = getattr(settings, 'BADGR_PUBLIC_BOT_USERAGENTS', ['LinkedInBot'])
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        if any(a in user_agent for a in bot_useragents):
            return True
        return False

    def is_wide_bot(self):
        """
        some bots prefer a wide aspect ratio for the image
        """
        bot_useragents = getattr(settings, 'BADGR_PUBLIC_BOT_USERAGENTS_WIDE', ['LinkedInBot'])
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        if any(a in user_agent for a in bot_useragents):
            return True
        return False

    def is_requesting_html(self):
        if self.format_kwarg == 'json':
            return False

        html_accepts = ['text/html']

        http_accept = self.request.META.get('HTTP_ACCEPT', 'application/json')

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
            redirect=redirect,
            path=stripped_path,
            query='?'+query_string if query_string else '')
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

        image_type = request.query_params.get('type', 'original')
        if image_type not in ['original', 'png']:
            raise ValidationError("invalid image type: {}".format(image_type))

        supported_fmts = {
            'square': (1, 1),
            'wide': (1.91, 1)
        }
        image_fmt = request.query_params.get('fmt', 'square').lower()
        if image_fmt not in list(supported_fmts.keys()):
            raise ValidationError("invalid image format: {}".format(image_fmt))

        image_url = image_prop.url
        filename, ext = os.path.splitext(image_prop.name)
        basename = os.path.basename(filename)
        dirname = os.path.dirname(filename)
        version_suffix = getattr(settings, 'CAIROSVG_VERSION_SUFFIX', '1')
        new_name = '{dirname}/converted{version}/{basename}{fmt_suffix}.png'.format(
            dirname=dirname,
            basename=basename,
            version=version_suffix,
            fmt_suffix="-{}".format(image_fmt) if image_fmt != 'square' else ""
        )
        storage = DefaultStorage()

        def _fit_to_height(img, ar, height=400):
            img.thumbnail((height,height))
            new_size = (int(ar[0]*height), int(ar[1]*height))
            new_img = Image.new("RGBA", new_size)
            new_img.paste(img, ((new_size[0] - height)/2, (new_size[1] - height)/2))
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


class IssuerJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = Issuer

    def log(self, obj):
        logger.event(badgrlog.IssuerRetrievedEvent(obj, self.request))

    def get_context_data(self, **kwargs):
        image_url = "{}{}?type=png".format(
            OriginSetting.HTTP,
            reverse('issuer_image', kwargs={'entity_id': self.current_object.entity_id})
        )
        if self.is_wide_bot():
            image_url = "{}&fmt=wide".format(image_url)

        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url
        )


class IssuerPublicKeyJson(IssuerJson):

    def get(self, request, **kwargs):
        self.current_object = self.get_object(request, **kwargs)
        self.log(self.current_object)

        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render_to_response(self.template_name, context=self.get_context_data())

        pubkey_issuer = PublicKeyIssuer.objects.get(entity_id=kwargs.get('public_key_id'))
        issuer_json = self.get_json(request=request, signed=True, public_key_issuer=pubkey_issuer, expand_public_key=False)
        return Response(issuer_json)


class IssuerBadgesJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = Issuer

    def log(self, obj):
        logger.event(badgrlog.IssuerBadgesRetrievedEvent(obj, self.request))

    def get_json(self, request):
        obi_version=self._get_request_obi_version(request)

        return [b.get_json(obi_version=obi_version) for b in self.current_object.cached_badgeclasses()]


class IssuerImage(ImagePropertyDetailView):
    model = Issuer
    prop = 'image'

    def log(self, obj):
        logger.event(badgrlog.IssuerImageRetrievedEvent(obj, self.request))


class BadgeClassJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = BadgeClass

    def log(self, obj):
        logger.event(badgrlog.BadgeClassRetrievedEvent(obj, self.request))

    def get_json(self, request):
        expands = request.GET.getlist('expand', [])
        json = super(BadgeClassJson, self).get_json(request)
        obi_version = self._get_request_obi_version(request)

        if 'issuer' in expands:
            json['issuer'] = self.current_object.cached_issuer.get_json(obi_version=obi_version)

        return json

    def get_context_data(self, **kwargs):
        image_url = "{}{}?type=png".format(
            OriginSetting.HTTP,
            reverse('badgeclass_image', kwargs={'entity_id': self.current_object.entity_id})
        )
        if self.is_wide_bot():
            image_url = "{}&fmt=wide".format(image_url)
        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url
        )


class BadgeClassPublicKeyJson(BadgeClassJson):

    def get(self, request, **kwargs):
        self.current_object = self.get_object(request, **kwargs)
        self.log(self.current_object)
        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render_to_response(self.template_name, context=self.get_context_data())

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
                expand_issuer=('badge.issuer' in expands)
            )
        return json

    def get_context_data(self, **kwargs):
        image_url = "{}{}?type=png".format(
            OriginSetting.HTTP,
            reverse('badgeclass_image', kwargs={'entity_id': self.current_object.cached_badgeclass.entity_id})
        )
        if self.is_wide_bot():
            image_url = "{}&fmt=wide".format(image_url)
        return dict(
            title=self.current_object.cached_badgeclass.name,
            description=self.current_object.cached_badgeclass.description,
            public_url=self.current_object.public_url,
            image_url=image_url
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
            raise ValidationError("Invalid OpenBadges version")

        # self.log(assertion)

        redirect_url = assertion.get_baked_image_url(obi_version=requested_version)

        return redirect(redirect_url, permanent=True)
