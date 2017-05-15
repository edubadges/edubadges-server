# encoding: utf-8
from __future__ import unicode_literals

import json
from collections import OrderedDict

from apispec import APISpec
from django.apps import apps
from importlib import import_module

from rest_framework.relations import RelatedField
from rest_framework.schemas import EndpointInspector
from rest_framework.serializers import ListSerializer, SerializerMetaclass


class BadgrAPISpec(APISpec):
    def __init__(self, version, *args, **kwargs):
        self.version = version
        title = kwargs.pop('title', 'Badgr {version} API'.format(version=version))
        super(BadgrAPISpec, self).__init__(title, version, *args, **kwargs)
        self.scrape_serializers()
        self.scrape_endpoints()

    def scrape_serializers(self):
        """
        Iterate over installed apps looking for serializers with Meta.apispec_definition
        """
        for app_config in apps.get_app_configs():
            module_name = '{app}.serializers_{version}'.format(app=app_config.name, version=self.version)
            try:
                app_serializer_module = import_module(module_name)
            except ImportError:
                pass
            else:
                for cls_name in dir(app_serializer_module):
                    cls = getattr(app_serializer_module, cls_name)

                    if isinstance(cls, SerializerMetaclass) and self.has_apispec_definition(cls):
                        definition_name, definition_kwargs = self.get_apispec_definition(cls)
                        self.serializer_definition(cls, definition_name, **definition_kwargs)

    def scrape_endpoints(self):
        """
        Iterate over the registered API endpoints for this version and generate path specs
        """
        inspector = EndpointInspector()
        for path, http_method, func in inspector.get_api_endpoints():
            if not path.startswith("/{}/".format(self.version)):  # skip if it doesnt match version
                continue
            http_method = http_method.lower()
            path_spec = {
                'path': path,
                'operations': {}
            }

            # View.as_view() returns a wrapper with .cls
            if hasattr(func, 'cls'):
                method_func = getattr(func.cls, http_method, None)
                if method_func is not None and hasattr(method_func, '_apispec_kwargs'):
                    # method was decorated with apispec_operation
                    operation = method_func._apispec_kwargs.copy()
                    path_spec['operations'][http_method] = operation
            self.add_path(**path_spec)

    def serializer_definition(self, serializer_class, name, **kwargs):
        """
        Add a definition based on a serializer class decorated with @apispec_definition
        """

        # populate default properties from serializer fields
        properties = OrderedDict()
        serializer = serializer_class()
        for field_name, field in serializer.get_fields().items():

            if isinstance(field, ListSerializer):
                field_properties = {
                    'type': "array",
                    'items': {
                        '$ref': "#/definitions/{}".format(self.get_ref_name(field.child.__class__))
                    }
                }
            elif isinstance(field, RelatedField):
                pass
            else:
                field_properties = {
                    'type': "string",  # TODO: Support numeric fields
                    'format': self.get_ref_name(field.__class__)
                }

            help_text = getattr(field, 'help_text', None)
            if help_text:
                field_properties['description'] = help_text

            properties[field_name] = field_properties

        #properties specified in kwargs override field defaults
        properties.update( kwargs.get('properties', {}) )
        kwargs['properties'] = properties

        self.definition(name, **kwargs)

    def has_apispec_definition(self, cls):
        return hasattr(cls, 'Meta') and hasattr(cls.Meta, 'apispec_definition')

    def get_apispec_definition(self, cls):
        if self.has_apispec_definition(cls):
            return cls.Meta.apispec_definition
        return None, {}

    def get_ref_name(self, cls):
        if self.has_apispec_definition(cls):
            definition_name, definition_kwargs = self.get_apispec_definition(cls)
            return definition_name
        else:
            return cls.__name__

    def write_to(self, outfile):
        outfile.write(json.dumps(self.to_dict(), indent=4))


