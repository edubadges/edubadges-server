# encoding: utf-8
from __future__ import unicode_literals

import cachemodel
import six
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django import http

from rest_framework import serializers, views, exceptions, status
from rest_framework.response import Response

from mainsite.utils import generate_entity_uri


class BaseVersionedEntity(cachemodel.CacheModel):
    entity_id = models.CharField(max_length=254, blank=False, null=True, default=None)
    entity_version = models.PositiveIntegerField(blank=False, null=False, default=1)

    class Meta:
        abstract = True

    def get_entity_class_name(self):
        if self.entity_class_name:
            return self.entity_class_name
        return self.__class__.__name__

    def save(self, *args, **kwargs):
        if self.entity_id is None:
            self.entity_id = generate_entity_uri(self.get_entity_class_name())

        self.entity_version += 1
        return super(BaseVersionedEntity, self).save(*args, **kwargs)

    def publish(self):
        super(BaseVersionedEntity, self).publish()
        self.publish_by('entity_id')

    def delete(self, *args, **kwargs):
        return super(BaseVersionedEntity, self).delete(*args, **kwargs)
        self.publish_delete('entity_id')


class EntityRelatedFieldV2(serializers.RelatedField):
    def __init__(self, *args, **kwargs):
        self.rel_source = kwargs.pop('rel_source', 'entity_id')
        super(EntityRelatedFieldV2, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        try:
            return self.get_queryset().get(**{self.rel_source: data})
        except ObjectDoesNotExist:
            self.fail('Invalid {rel_source} "{rel_value}" - object does not exist.', rel_source=self.rel_source, rel_value=data)
        except (TypeError, ValueError):
            self.fail('Incorrect type. Expected {rel_source} value, received {data_type}.', rel_source=self.rel_source, data_type=type(data).__name__)

    def to_representation(self, value):
        return getattr(value, self.rel_source)


class BaseSerializerV2(serializers.Serializer):
    _success = True
    _description = "ok"

    @property
    def success(self):
        return self._success

    @success.setter
    def success(self, value):
        self._success = value

    @property
    def description(self):
        return self._description

    @description.setter
    def description(self, value):
        self._description = value

    def __init__(self, *args, **kwargs):
        self.success = kwargs.pop('success', True)
        self.description = kwargs.pop('description', 'ok')
        super(BaseSerializerV2, self).__init__(*args, **kwargs)

    @staticmethod
    def response_envelope(result, success, description, field_errors=None, validation_errors=None):
        # assert isinstance(result, collections.Sequence)

        envelope = {
            "status": {
                "success": success,
                "description": description
            },
            "result": result
        }

        if field_errors is not None:
            envelope["fieldErrors"] = field_errors

        if validation_errors is not None:
            envelope["validationErrors"] = validation_errors

        return envelope


class ListSerializerV2(serializers.ListSerializer, BaseSerializerV2):
    def to_representation(self, instance):
        representation = super(ListSerializerV2, self).to_representation(instance)
        if self.parent is not None:
            return representation
        else:
            return BaseSerializerV2.response_envelope(result=representation,
                                                      success=self.success,
                                                      description=self.description)

    @property
    def data(self):
        return super(serializers.ListSerializer, self).data


class DetailSerializerV2(BaseSerializerV2):
    entityId = serializers.CharField(source='entity_id', max_length=254, read_only=True)

    def to_representation(self, instance):
        representation = super(DetailSerializerV2, self).to_representation(instance)
        if self.parent is not None:
            return representation
        else:
            return BaseSerializerV2.response_envelope(result=[representation],
                                                      success=self.success,
                                                      description=self.description)

    class Meta:
        list_serializer_class = ListSerializerV2


class V2ErrorSerializer(BaseSerializerV2):
    _field_errors = {}
    _validation_errors = []

    @property
    def field_errors(self):
        return self._field_errors

    @field_errors.setter
    def field_errors(self, value):
        self._field_errors = value

    @property
    def validation_errors(self):
        return self._validation_errors

    @validation_errors.setter
    def validation_errors(self, value):
        self._validation_errors = value

    def __init__(self, *args, **kwargs):
        self.field_errors = kwargs.pop('field_errors', False)
        self.validation_errors = kwargs.pop('validation_errors', 'error')
        super(V2ErrorSerializer, self).__init__(*args, **kwargs)

    def to_representation(self, instance):
        return BaseSerializerV2.response_envelope(result=[],
                                                  success=self.success,
                                                  description=self.description,
                                                  field_errors=self.field_errors,
                                                  validation_errors=self.validation_errors)


def exception_handler(exc, context):
    version = context.get('kwargs', None).get('version', 'v1')
    if version == 'v1':
        # Use the default exception-handling logic for v1
        return views.exception_handler(exc, context)
    elif version == 'v2':
        description = 'miscellaneous error'
        field_errors = {}
        validation_errors = []
        response_code = None
        if isinstance(exc, exceptions.ParseError):
            description = 'bad request'
            validation_errors = [exc.detail]

        elif isinstance(exc, exceptions.ValidationError):
            description = 'bad request'

            if isinstance(exc.detail, list):
                validation_errors = exc.detail
            elif isinstance(exc.detail, dict):
                field_errors = exc.detail
            elif isinstance(exc.detail, six.string_types):
                validation_errors = [exc.detail]

            response_code = status.HTTP_400_BAD_REQUEST

        elif isinstance(exc, (exceptions.AuthenticationFailed, exceptions.NotAuthenticated)):
            description = 'no valid auth token found'
            response_code = status.HTTP_401_UNAUTHORIZED

        elif isinstance(exc, (http.Http404, exceptions.PermissionDenied)):
            description = 'entity not found or insufficient privileges'
            response_code = status.HTTP_404_NOT_FOUND

        elif isinstance(exc, exceptions.APIException):
            field_errors = exc.detail
            response_code = exc.status_code

        else:
            # Unrecognized exception, return 500 error
            return None


        serializer = V2ErrorSerializer(instance={},
                                       success=False,
                                       description=description,
                                       field_errors=field_errors,
                                       validation_errors=validation_errors)

        return Response(serializer.data, status=response_code)