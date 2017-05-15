# encoding: utf-8
from __future__ import unicode_literals

import json

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
        Iterate over installed apps looking for serializers decorated with @apispec_definition
        """
        for app_config in apps.get_app_configs():
            module_name = '{app}.serializers_{version}'.format(app=app_config.name, version=self.version)
            try:
                if module_name == 'issuer.serializers_v2':
                    pass
                app_serializer_module = import_module(module_name)
            except ImportError:
                pass
            else:
                for func_name in dir(app_serializer_module):
                    func = getattr(app_serializer_module, func_name)
                    if hasattr(func, '_apispec_wrapped'):
                        self.serializer_definition(func)

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

    def serializer_definition(self, serializer_class):
        """
        Add a definition based on a serializer class decorated with @apispec_definition 
        """
        if serializer_class is not None:
            apispec_args = getattr(serializer_class, '_apispec_args', [])
            apispec_kwargs = getattr(serializer_class, '_apispec_kwargs', {})
            self.definition(*apispec_args, **apispec_kwargs)

    def write_to(self, outfile):
        outfile.write(json.dumps(self.to_dict(), indent=4))


