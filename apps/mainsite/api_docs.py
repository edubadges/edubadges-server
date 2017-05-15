# encoding: utf-8
from __future__ import unicode_literals

import json
from collections import OrderedDict

from apispec import APISpec
from django.apps import apps
from importlib import import_module
from rest_framework.schemas import EndpointInspector


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
                for serializer_class_name in dir(app_serializer_module):
                    serializer_class = getattr(app_serializer_module, serializer_class_name)
                    if hasattr(serializer_class, 'Meta') and hasattr(serializer_class.Meta, 'apispec_definition'):
                        definition_name, definition_kwargs = serializer_class.Meta.apispec_definition
                        self.serializer_definition(serializer_class, definition_name, **definition_kwargs)

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
            help_text = getattr(field, 'help_text', None)
            properties[field_name] = {
                'type': "string",
                'format': field.__class__.__name__,  # fixme
            }
            if help_text:
                properties['description'] = help_text

        #properties specified in kwargs override field defaults
        properties.update( kwargs.get('properties', {}) )
        kwargs['properties'] = properties

        self.definition(name, **kwargs)

    def write_to(self, outfile):
        outfile.write(json.dumps(self.to_dict(), indent=4))


