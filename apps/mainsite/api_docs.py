# encoding: utf-8
from __future__ import unicode_literals

import json
import re
from collections import OrderedDict

import six
from apispec import APISpec
from django.apps import apps
from importlib import import_module

from rest_framework.fields import Field
from rest_framework.relations import RelatedField
from rest_framework.schemas import EndpointInspector
from rest_framework.serializers import ListSerializer, SerializerMetaclass, BaseSerializer


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
                        serializer_spec = self.get_serializer_spec(cls)
                        merged_spec = self.merge_specs(serializer_spec, definition_kwargs)

                        #TODO: Is it possible to avoid the sillyness below required to extract extra_fields?
                        self.definition(definition_name,
                                        properties=merged_spec.pop('properties', None),
                                        enum=merged_spec.pop('enum', None),
                                        merged_spec=merged_spec.pop('description', None),
                                        extra_fields=merged_spec)

    def get_path_parameters(self, path):
        """
        Accepts a path with curly bracket-delimited parameters and returns a list of parameter names.

        For example:

        extract_path_parameters("/{foo}/bar/{baz}") -> [foo, baz]
        """
        return re.findall('{([^{]*)}', path)

    def get_path_parameter_list(self, path):
        return [{
            'in': 'path',
            'name': param,
            'required': True,
            'type': "string"
        } for param in self.get_path_parameters(path)]

    def scrape_endpoints(self):
        """
        Iterate over the registered API endpoints for this version and generate path specs
        """
        inspector = EndpointInspector()
        for path, http_method, func in inspector.get_api_endpoints():
            http_method = http_method.lower()

            if not path.startswith("/{}/".format(self.version)):  # skip if it doesnt match version
                continue

            method_func = getattr(func.cls, http_method, None)
            if self.has_apispec_wrapper(method_func):
                operation_spec = self.get_operation_spec(path, http_method, method_func)
                merged_spec = self.merge_specs(operation_spec, self.get_apispec_kwargs(method_func))

                path_spec = {
                    'path': path,
                    'operations': {
                        http_method: merged_spec
                    }
                }
                self.add_path(**path_spec)

    def has_apispec_wrapper(self, method_func):
        return hasattr(method_func, '_apispec_wrapped')

    def get_apispec_args(self, method_func):
        if self.has_apispec_wrapper(method_func):
            return method_func._apispec_args
        return []

    def get_apispec_kwargs(self, method_func):
        if self.has_apispec_wrapper(method_func):
            return method_func._apispec_kwargs
        return {}

    @staticmethod
    def merge_specs(base, override):
        """
        Apply override dict on top of base dict up to a depth of 1.

        Dictionary values are updated on a per-key basis in the merged list.  Lists values are concatenated.
        """
        merged = base.copy()

        for key, override_value in override.items():
            if key not in base:
                merged[key] = override_value
            else:
                base_value = base[key]
                if isinstance(override_value, dict) and isinstance(base_value, dict):
                    merged[key].update(override_value)
                elif isinstance(override_value, list) and isinstance(base_value, list):
                    merged[key] = base_value + override_value
                else:
                    raise ValueError("Base and override values are not of same type")

        return merged

    def get_operation_spec(self, path, http_method, method_func):
        return {
            'parameters': self.get_path_parameter_list(path)
        }

    def get_field_property(self, field):
        assert isinstance(field, Field)

        if isinstance(field, ListSerializer):
            field_properties = {
                'type': "array",
                'items': {
                    '$ref': "#/definitions/{}".format(self.get_ref_name(field.child.__class__))
                }
            }
        else:
            field_properties = {
                'type': "string",  # TODO: Support numeric fields
                'format': self.get_ref_name(field.__class__)
            }

        help_text = getattr(field, 'help_text', None)
        if help_text:
            field_properties['description'] = help_text

        return field_properties

    def get_required_properties(self, serializer):
        return [field_name for field_name, field in serializer.get_fields().items() if field.required]

    def get_serializer_properties(self, serializer):
        assert isinstance(serializer, BaseSerializer)

        return {
            field_name: self.get_field_property(field)
            for field_name, field in serializer.get_fields().items()
        }

    def get_serializer_spec(self, serializer_class):
        """
        Generate a definition based on a serializer class decorated with @apispec_definition
        """
        return {
            'properties': self.get_serializer_properties(serializer_class()),
            'required': self.get_required_properties(serializer_class())
        }

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


