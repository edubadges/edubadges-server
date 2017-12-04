import StringIO
import os
import re

import cairosvg
from PIL import Image
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import resolve, reverse, Resolver404, NoReverseMatch
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect, render_to_response
from django.views.generic import RedirectView
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

import badgrlog
import utils
from backpack.models import BackpackCollection
from entity.api import VersionedObjectMixin
from mainsite.models import BadgrApp
from mainsite.utils import OriginSetting
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
        if getattr(self.current_object, 'source_url', None) and getattr(self.current_object, 'original_json', None):
            json = self.current_object.get_original_json()
        else:
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

        self.log(self.current_object)

        if self.is_bot():
            # if user agent matches a known bot, return a stub html with opengraph tags
            return render_to_response(self.template_name, context=self.get_context_data())

        if self.is_requesting_html():
            return HttpResponseRedirect(redirect_to=self.get_badgrapp_redirect())

        json = self.get_json(request=request)
        return Response(json)

    def is_bot(self):
        bot_useragents = getattr(settings, 'BADGR_PUBLIC_BOT_USERAGENTS', ['LinkedInBot'])
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        if any(a in user_agent for a in bot_useragents):
            return True
        return False

    def is_requesting_html(self):
        if self.format_kwarg == 'json':
            return False

        html_accepts = ['*/*', 'text/html']

        http_accept = self.request.META.get('HTTP_ACCEPT', 'application/json')

        if self.is_bot() or any(a in http_accept for a in html_accepts):
            return True

        return False

    def get_badgrapp_redirect(self):
        badgrapp = self.current_object.cached_badgrapp
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
            self.log(current_object)
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
            raise ValidationError(u"invalid image type: {}".format(image_type))

        image_url = image_prop.url
        filename, ext = os.path.splitext(image_prop.name)
        basename = os.path.basename(filename)
        dirname = os.path.dirname(filename)
        version_suffix = getattr(settings, 'CAIROSVG_VERSION_SUFFIX', '1')
        new_name = '{dirname}/converted{version}/{basename}.png'.format(dirname=dirname, basename=basename, version=version_suffix)
        storage = DefaultStorage()

        if image_type == 'original':
            image_url = image_prop.url
        elif image_type == 'png' and ext == '.svg':
            if not storage.exists(new_name):
                with storage.open(image_prop.name, 'rb') as input_svg:
                    svg_buf = StringIO.StringIO()
                    out_buf = StringIO.StringIO()
                    cairosvg.svg2png(file_obj=input_svg, write_to=svg_buf)
                    img = Image.open(svg_buf)
                    img.thumbnail((400, 400))
                    img.save(out_buf, format=image_type)
                    storage.save(new_name, out_buf)
            image_url = storage.url(new_name)
        elif ext != '.png':
            # attempt to use PIL to do desired image conversion
            if not storage.exists(new_name):
                with storage.open(image_prop.name, 'rb') as input_svg:
                    out_buf = StringIO.StringIO()
                    img = Image.open(input_svg)
                    img.save(out_buf, format=image_type)
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
        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url
        )


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
        return dict(
            title=self.current_object.name,
            description=self.current_object.description,
            public_url=self.current_object.public_url,
            image_url=image_url
        )


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
    permission_classes = (permissions.AllowAny,)
    model = BadgeInstance

    def get_json(self, request):
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


class BackpackCollectionJson(JSONComponentView):
    permission_classes = (permissions.AllowAny,)
    model = BackpackCollection
    entity_id_field_name = 'share_hash'

    def get_json(self, request):
        expands = request.GET.getlist('expand', [])
        if not self.current_object.published:
            raise Http404

        json = self.current_object.get_json(
            obi_version=self._get_request_obi_version(request),
            expand_badgeclass=('badges.badge' in expands),
            expand_issuer=('badges.badge.issuer' in expands)
        )
        return json
