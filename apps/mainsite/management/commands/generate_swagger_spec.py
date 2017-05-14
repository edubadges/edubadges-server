# encoding: utf-8
from __future__ import unicode_literals

import json

from django.core.management import BaseCommand
from apispec import APISpec
from mainsite import __version__
from rest_framework.schemas import EndpointInspector


class Command(BaseCommand):
    def handle(self, *args, **options):

        spec = APISpec(
            title='Badgr',
            version=__version__,
            info=dict(
                description='Badgr API Docs preamble'
            )
        )

        inspector = EndpointInspector()
        for path, http_method, func in inspector.get_api_endpoints():
            http_method = http_method.lower()
            path_spec = {
                'path': path,
                'operations': {}
            }
            if hasattr(func, 'cls'):
                method_func = getattr(func.cls, http_method, None)
                if method_func is not None and hasattr(method_func, '_apispec_operation'):
                    path_spec['operations'][http_method] = method_func._apispec_operation['kwargs'].copy()
            spec.add_path(**path_spec)


        # FIXME: example
        spec.definition('Issuer', properties={
            'entity_id': {
                'type': 'string',
                'description': "Entity Id for the issuer"
            },
            'name': {
                'type': 'string',
                'description': "The name of the issuer"
            }
        }),

        self.stdout.write( json.dumps(spec.to_dict()) )
        pass
