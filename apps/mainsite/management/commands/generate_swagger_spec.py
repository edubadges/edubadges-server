# encoding: utf-8
from __future__ import unicode_literals

import json
from collections import OrderedDict

import os
from django.conf import settings
from django.core.management import BaseCommand
from apispec import APISpec
from django.core.management.base import LabelCommand
from django.utils.module_loading import import_string
from mainsite import __version__, TOP_DIR
from rest_framework.schemas import EndpointInspector


class BadgrAPISpec(APISpec):
    def __init__(self, *args, **kwargs):
        super(BadgrAPISpec, self).__init__(*args, **kwargs)
        self._definitions = OrderedDict()


class Command(BaseCommand):

    def add_arguments(self, parser):
        default_out = os.path.join(TOP_DIR, 'breakdown', 'static', 'swagger-ui')
        parser.add_argument('--output', nargs='?', default=default_out)
        parser.add_argument('--output-filename', nargs='?', default='{version}_badgr_spec.json')
        parser.add_argument('versions', nargs='*')

    def handle(self, *args, **options):
        versions = options.get('versions', [])
        if len(versions) < 1:
            versions = ['v1', 'v2']
        for version in versions:
            output_path = os.path.join(options['output'], options['output_filename'].format(version=version))
            with open(output_path, 'w') as spec_file:
                if options['verbosity'] > 0:
                    self.stdout.write("Generating '{}' spec in '{}'".format(version, output_path))
                self.generate_spec_for_version(version, spec_file)

    def generate_spec_for_version(self, version, outfile):
        spec = BadgrAPISpec(
            title='Badgr',
            version=__version__,
            info=dict(
                description='Badgr API Docs preamble'
            )
        )

        definitions_idx = {}

        # any extra serializers that dont appear as an endpoints .model
        extra_serializers = getattr(settings, '{}_DOC_SERIALIZERS'.format(version.upper()), [])
        for serializer_cls_name in extra_serializers:
            serializers_cls = import_string(serializer_cls_name)
            self.add_serializer_to_spec(spec, serializers_cls)

        # iterate over the api endpoints
        inspector = EndpointInspector()
        for path, http_method, func in inspector.get_api_endpoints():
            if not path.startswith("/{}/".format(version)):  # skip if it doesnt match version
                continue
            http_method = http_method.lower()
            path_spec = {
                'path': path,
                'operations': {}
            }
            if hasattr(func, 'cls'):
                # View.as_view() returns a wrapper with .cls

                # load the version serializer class and add a definition for it if needed
                if hasattr(func.cls, '{}_serializer_class'.format(version)):
                    serializer_class = getattr(func.cls, '{}_serializer_class'.format(version), None)
                    if serializer_class is not None and serializer_class not in definitions_idx:
                        definitions_idx[serializer_class] = True
                        self.add_serializer_to_spec(spec, serializer_class)

                # add operation if method is decorated
                method_func = getattr(func.cls, http_method, None)
                if method_func is not None and hasattr(method_func, '_apispec_kwargs'):
                    operation = method_func._apispec_kwargs.copy()
                    path_spec['operations'][http_method] = operation
            spec.add_path(**path_spec)

        outfile.write( json.dumps(spec.to_dict()) )

    def add_serializer_to_spec(self, spec, serializer_class):
        if serializer_class is not None and hasattr(serializer_class, '_apispec_wrapped'):
            spec.definition(*serializer_class._apispec_args, **serializer_class._apispec_kwargs)
