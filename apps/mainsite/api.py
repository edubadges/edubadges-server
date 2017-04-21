# encoding: utf-8
from __future__ import unicode_literals

from django.http import Http404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class BaseEntityView(APIView):
    def get_context_data(self, **kwargs):
        return {
            'request': self.request,
            'kwargs': kwargs,
        }

    def get_serializer_class(self):
        if self.request.version == 'v1' and hasattr(self, 'v1_serializer_class'):
            return self.v1_serializer_class
        elif self.request.version == 'v2' and hasattr(self, 'v2_serializer_class'):
            return self.v2_serializer_class
        return getattr(self, 'serializer_class', None)


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
        return Response(serializer.data)

    def post(self, request, **kwargs):
        """
        POST a new entity to be owned by the authenticated user
        """

        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BaseEntityDetailView(BaseEntityView):
    def get_object(self, request, **kwargs):
        version = getattr(request, 'version', 'v1')
        if version == 'v1':
            lookup_kwargs = {
                'slug': kwargs.get('slug')
            }
        elif version == 'v2':
            lookup_kwargs = {
                'entity_id': kwargs.get('entity_id')
            }

        try:
            self.object = self.model.cached.get(**lookup_kwargs)
        except self.model.DoesNotExist:
            raise Http404
        else:
            return self.object

    def has_object_permissions(self, request, obj):
        for permission in self.get_permissions():
            if not permission.has_object_permission(request, self, obj):
                return False
            return True

    def get(self, request, **kwargs):
        """
        GET a single entity by its identifier 
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=status.HTTP_404_NOT_FOUND)

        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj, context=context)
        return Response(serializer.data)

    def put(self, request, **kwargs):
        """
        PUT a new version of an entity
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=status.HTTP_404_NOT_FOUND)

        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(obj, data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save(updated_by=request.user)
        return Response(serializer.data)

    def delete(self, request, **kwargs):
        """
        DELETE a single entity by identifier
        """
        obj = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, obj):
            return Response(status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_200_OK)


