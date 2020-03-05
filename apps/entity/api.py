# encoding: utf-8


import logging

import badgrlog
from django.core.exceptions import FieldError
from django.http import Http404
from mainsite.pagination import EncryptedCursorPagination
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_201_CREATED, HTTP_204_NO_CONTENT
from rest_framework.views import APIView

logger=logging.getLogger('Badgr.Debug')

class LogPermissionsFailMixin():
    def check_permissions(self, request):
        """
        Overrides check permissions to log when permission fails
        """
        for permission in self.get_permissions():
            if not permission.has_permission(request, self):
                logger.error({'permission.message':permission.message,
                              "request.path": request.path})
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )
    

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
        serializer.is_valid(raise_exception=True)
        new_instance = serializer.save(created_by=request.user)
        self.log_create(new_instance)
        return Response(serializer.data, status=HTTP_201_CREATED)


class VersionedObjectMixin(object):
    entity_id_field_name = 'entity_id'

    def has_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                return False
        return True

    def get_object(self, request, **kwargs):
        version = getattr(request, 'version', 'v1')
        if version == 'v1':
            identifier = kwargs.get('slug')
        elif version == 'v2':
            identifier = kwargs.get('entity_id')

        try:
            self.object = self.model.cached.get(**{self.get_entity_id_field_name(): identifier})
        except self.model.DoesNotExist:
            pass
        else:
            if not self.has_object_permissions(request, self.object):
                raise Http404
            return self.object

        if version == 'v1':
            # try a lookup by legacy slug if its v1
            try:
                self.object = self.model.cached.get(slug=identifier)
            except (self.model.DoesNotExist, FieldError):
                raise Http404
            else:
                if not self.has_object_permissions(request, self.object):
                    raise Http404
                return self.object

        # nothing found
        raise Http404

    def get_entity_id_field_name(self):
        return self.entity_id_field_name


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
        serializer.is_valid(raise_exception=True)
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


class UncachedPaginatedViewMixin(object):
    min_per_page = 1
    max_per_page = 500
    default_per_page = None  # dont paginate by default
    per_page_query_parameter_name = 'num'

    def get_queryset(self, request, **kwargs):
        raise NotImplementedError

    def get_objects(self, request, **kwargs):
        queryset = self.get_queryset(request=request, **kwargs)

        try:
            per_page = int(request.query_params.get(self.per_page_query_parameter_name, self.default_per_page))
            per_page = max(self.min_per_page, per_page)
            per_page = min(self.max_per_page, per_page)
        except (TypeError, ValueError):
            per_page = None

        # only paginate on request
        if per_page:
            self.paginator = EncryptedCursorPagination()
            self.paginator.page_size = per_page
            page = self.paginator.paginate_queryset(queryset, request=request)
        else:
            page = list(queryset)

        return page
