# encoding: utf-8

from django.http import Http404
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

import badgrlog
from entity.utils import validate_errors


class BaseEntityView(APIView):
    create_event = None
    logger = None
    permission_map = {'GET': 'may_read', 'POST': 'may_create',
                      'PUT': 'may_update', 'DELETE': 'may_delete'}

    def get_context_data(self, **kwargs):
        return {
            'request': self.request,
            'kwargs': kwargs,
        }

    def get_serializer_class(self):
        if self.request.version == 'v1' and hasattr(self, 'v1_serializer_class'):
            return self.v1_serializer_class
        # elif self.request.version == 'v2' and hasattr(self, 'v2_serializer_class'):
        #     return self.v2_serializer_class
        return getattr(self, 'serializer_class', None)

    def get_logger(self):
        if self.logger:
            return self.logger
        self.logger = badgrlog.BadgrLogger()
        return self.logger

    def get_create_event(self):
        return getattr(self, 'create_event', None)

    def log_create(self, instance):
        event_cls = self.get_create_event()
        if event_cls is not None:
            logger = self.get_logger()
            if logger is not None:
                logger.event(event_cls(instance))


class BaseEntityListView(BaseEntityView):

    def get_objects(self, request, **kwargs):
        raise NotImplementedError

    def get(self, request, **kwargs):
        """
        GET a list of an entities the authenticated user is authorized for
        """
        objects = self.get_objects(request, **kwargs)
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(objects, many=True, context=context)

        headers = dict()
        paginator = getattr(self, 'paginator', None)
        if paginator and callable(getattr(paginator, 'get_link_header', None)):
            link_header = paginator.get_link_header()
            if link_header:
                headers['Link'] = link_header

        return Response(serializer.data, headers=headers)

    def post(self, request, **kwargs):
        """
        POST a new entity to be owned by the authenticated user
        """
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context=context)
        validate_errors(serializer)

        new_instance = serializer.save(created_by=request.user)
        self.log_create(new_instance)
        return Response(serializer.data, status=HTTP_201_CREATED)


class VersionedObjectMixin(object):

    def has_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                return False
        return True

    def get_object(self, request, **kwargs):
        identifier = kwargs.get('entity_id')
        bypass_cache = kwargs.get('bypass_cache', False)
        try:
            self.object = self.model.objects.get(
                **{'entity_id': identifier}) if bypass_cache else self.model.cached.get(**{'entity_id': identifier})
        except self.model.DoesNotExist:
            pass
        else:
            if not self.has_object_permissions(request, self.object):
                raise Http404
            return self.object

        # nothing found
        raise Http404


class BaseEntityDetailView(BaseEntityView, VersionedObjectMixin):

    def get(self, request, **kwargs):
        """
        GET a single entity by its identifier
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=HTTP_404_NOT_FOUND)

        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj, context=context)
        return Response(serializer.data)

    def put(self, request, data=None, allow_partial=False, **kwargs):
        """
        PUT a new version of an entity
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=HTTP_404_NOT_FOUND)

        if data is None:
            data = request.data

        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj, data=data, partial=allow_partial, context=context)
        validate_errors(serializer)

        serializer.save(updated_by=request.user)
        return Response(serializer.data)

    def delete(self, request, **kwargs):
        """
        DELETE a single entity by identifier
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=HTTP_204_NO_CONTENT)
