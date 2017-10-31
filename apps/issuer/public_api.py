import StringIO
import re

import cairosvg
import os
from PIL import Image
from django.conf import settings
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import resolve, reverse, Resolver404, NoReverseMatch
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import RedirectView
from rest_framework import status, permissions
from rest_framework.exceptions import ValidationError
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

import badgrlog
import utils
from backpack.models import BackpackCollection
from entity.api import VersionedObjectMixin
from mainsite.models import BadgrApp
from .models import Issuer, BadgeClass, BadgeInstance
from .renderers import BadgeInstanceHTMLRenderer, BadgeClassHTMLRenderer, IssuerHTMLRenderer

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
            return redirect(redirect_url, permanent=True)
        else:
            raise Http404


class JSONComponentView(VersionedObjectMixin, APIView, SlugToEntityIdRedirectMixin):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)
    html_renderer_class = None

    def log(self, obj):
        pass

    def get(self, request, **kwargs):
        try:
            self.current_object = self.get_object(request, **kwargs)
        except Http404:
            if self.slugToEntityIdRedirect:
                return self.get_slug_to_entity_id_redirect(kwargs.get('entity_id', None))
            else:
                raise

        self.log(self.current_object)

        if self.is_requesting_html():
            return HttpResponseRedirect(redirect_to=self.get_badgrapp_redirect())

        # render public JSON
        if getattr(self.current_object, 'source_url', None) and getattr(self.current_object, 'original_json', None):
            json = self.current_object.get_original_json()
        else:
            json = self.current_object.get_json(obi_version=self._get_request_obi_version(request))
        return Response(json)

    def is_requesting_html(self):
        if self.format_kwarg == 'json':
            return False

        HTTP_USER_AGENTS = ['LinkedInBot',]
        HTTP_ACCEPTS = ['*/*', 'text/html']

        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        http_accept = self.request.META.get('HTTP_ACCEPT', '*/*')

        if any(a in user_agent for a in HTTP_USER_AGENTS) or any(a in http_accept for a in HTTP_ACCEPTS):
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
        return redirect+stripped_path

    @staticmethod
    def _get_request_obi_version(request):
        return request.query_params.get('v', utils.CURRENT_OBI_VERSION)


class ComponentPropertyDetailView(APIView):
    """
    Abstract Component Class
    """
    permission_classes = (permissions.AllowAny,)

    def log(self, obj):
        pass

    def get(self, request, slug):
        try:
            current_object = self.model.cached.get(slug=slug)
        except self.model.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            self.log(current_object)

        p = getattr(current_object, self.prop)
        if not bool(p):
            return Response(status=status.HTTP_404_NOT_FOUND)
        return redirect(p.url)


class ImagePropertyDetailView(ComponentPropertyDetailView, SlugToEntityIdRedirectMixin):
    """
    a subclass of ComponentPropertyDetailView, for image fields, if query_param type='png' re-encode if necessary
    """
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


class BackpackCollectionJson(JSONComponentView):
    model = BackpackCollection
    entity_id_field_name = 'share_hash'


class IssuerJson(JSONComponentView):
    """
    GET the actual OBI badge object for an issuer via the /public/issuers/ endpoint
    """
    model = Issuer
    renderer_classes = (JSONRenderer, IssuerHTMLRenderer,)
    html_renderer_class = IssuerHTMLRenderer

    def log(self, obj):
        logger.event(badgrlog.IssuerRetrievedEvent(obj, self.request))

    def get_renderer_context(self, **kwargs):
        context = super(IssuerJson, self).get_renderer_context(**kwargs)
        if getattr(self, 'current_object', None):
            context['issuer'] = self.current_object
            context['badge_classes'] = self.current_object.cached_badgeclasses()
            context['badgeclass_count'] = len(self.current_object.cached_badgeclasses())
        return context


class IssuerImage(ImagePropertyDetailView):
    """
    GET an image that represents an Issuer
    """
    model = Issuer
    prop = 'image'

    def log(self, obj):
        logger.event(badgrlog.IssuerImageRetrievedEvent(obj, self.request))


class BadgeClassJson(JSONComponentView):
    """
    GET the actual OBI badge object for a badgeclass via public/badges/:slug endpoint
    """
    model = BadgeClass
    renderer_classes = (JSONRenderer, BadgeClassHTMLRenderer,)
    html_renderer_class = BadgeClassHTMLRenderer

    def get_renderer_context(self, **kwargs):
        context = super(BadgeClassJson, self).get_renderer_context(**kwargs)
        if getattr(self, 'current_object', None):
            context['badge_class'] = self.current_object
            context['issuer'] = self.current_object.cached_issuer
            context['badgeclass_count'] = len(context['issuer'].cached_badgeclasses())
        return context

    def log(self, obj):
        logger.event(badgrlog.BadgeClassRetrievedEvent(obj, self.request))


class BadgeClassImage(ImagePropertyDetailView):
    """
    GET the unbaked badge image from a pretty url instead of media path
    """
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
    model = BadgeInstance
    renderer_classes = (JSONRenderer, BadgeInstanceHTMLRenderer,)
    html_renderer_class = BadgeInstanceHTMLRenderer
    permission_classes = (permissions.AllowAny,)

    def get_renderer_context(self, **kwargs):
        context = super(BadgeInstanceJson, self).get_renderer_context()
        context['obi_version'] = self._get_request_obi_version(self.request)

        if getattr(self, 'current_object', None):
            context['badge_instance'] = self.current_object
            context['badge_class'] = self.current_object.cached_badgeclass
            context['issuer'] = self.current_object.cached_issuer
            context['badgeclass_count'] = len(context['issuer'].cached_badgeclasses())

        if self.request.query_params.get('action', None) == 'download':
            context['action'] = 'download'

        return context

    def get(self, request, **kwargs):
        try:
            current_object = self.get_object(request, **kwargs)
            self.current_object = current_object
        except Http404:
            if self.slugToEntityIdRedirect:
                return self.get_slug_to_entity_id_redirect(kwargs.get('entity_id', None))
            else:
                raise

        if current_object.revoked is False:

            logger.event(badgrlog.BadgeAssertionCheckedEvent(current_object, request))
            if current_object.source_url and current_object.original_json:
                json = current_object.get_original_json()
            else:
                json = current_object.get_json(obi_version=self._get_request_obi_version(request))
            return Response(json)
        else:
            # TODO update terms based on final accepted terms in response to
            # https://github.com/openbadges/openbadges-specification/issues/33
            revocation_info = {
                '@context': utils.CURRENT_OBI_CONTEXT_IRI,
                'id': current_object.jsonld_id,
                'revoked': True,
                'revocationReason': current_object.revocation_reason
            }

            logger.event(badgrlog.RevokedBadgeAssertionCheckedEvent(current_object, request))
            return Response(revocation_info, status=status.HTTP_410_GONE)


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

