# encoding: utf-8
from __future__ import unicode_literals

import os
from django.core.management import BaseCommand
from mainsite import TOP_DIR

from mainsite.api_docs import BadgrAPISpec


class Command(BaseCommand):

    def add_arguments(self, parser):
        default_out = os.path.join(TOP_DIR, 'breakdown', 'static', 'swagger-ui')
        parser.add_argument('--output', nargs='?', default=default_out)
        parser.add_argument('--output-filename', nargs='?', default='badgr_spec_{version}.json')
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
                spec = BadgrAPISpec(version=version)
                spec.write_to(spec_file)


