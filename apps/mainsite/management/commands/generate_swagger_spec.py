# encoding: utf-8
from __future__ import unicode_literals

import json

from django.core.management import BaseCommand
from apispec import APISpec
from mainsite import __version__


class Command(BaseCommand):
    def handle(self, *args, **options):

        spec = APISpec(
            title='Badgr',
            version=__version__,
            info=dict(
                description='Badgr API Docs preamble'
            )
        )

        # FIXME: examples from apispec quickstart demos
        spec.definition('Gist', properties={
            'id': {
                'type': 'integer',
                'format': 'int64'
            },
            'content': {
                'type': 'string'
            }
        }),
        spec.add_path(
            path='/gist/{gist_id}',
            operations=dict(
                get=dict(
                    responses={
                        '200': {
                            'schema': {'$ref': '#/definitions/Gist'}
                        }
                    }
                )
            )
        )

        self.stdout.write( json.dumps(spec.to_dict()) )
        pass
