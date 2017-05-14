# encoding: utf-8
from __future__ import unicode_literals

import json

from django.core.management import BaseCommand
from apispec import APISpec
from mainsite import __version__
from rest_framework.schemas import EndpointInspector


class Command(BaseCommand):
    def handle(self, *args, **options):

        version = "v2"

        spec = APISpec(
            title='Badgr',
            version=__version__,
            info=dict(
                description='Badgr API Docs preamble'
            )
        )

        definitions_idx = {}

        inspector = EndpointInspector()
        for path, http_method, func in inspector.get_api_endpoints():
            if not path.startswith("/{}/".format(version)):
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
                    if serializer_class is not None and \
                            serializer_class not in definitions_idx and \
                            hasattr(serializer_class, '_apispec_wrapped'):
                        definitions_idx[serializer_class] = True
                        spec.definition(*serializer_class._apispec_args,
                                        **serializer_class._apispec_kwargs)

                # make a
                method_func = getattr(func.cls, http_method, None)
                if method_func is not None and hasattr(method_func, '_apispec_kwargs'):
                    operation = method_func._apispec_kwargs.copy()
                    path_spec['operations'][http_method] = operation
            spec.add_path(**path_spec)

        self.stdout.write( json.dumps(spec.to_dict()) )
        pass
