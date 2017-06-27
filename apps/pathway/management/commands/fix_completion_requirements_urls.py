import logging
import re

from django.conf import settings
from django.core.management.base import BaseCommand

from pathway.models import PathwayElement

logger = logging.getLogger('command')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class Command(BaseCommand):
    help = 'Perform prefix substitution of badge URLs in pathway completion requirements'

    def add_arguments(self, parser):
        parser.add_argument('--url-match-prefix', required=True)
        parser.add_argument('--url-substitute-prefix', required=True)
        parser.add_argument('--dry-run', action='store_true', default=False)

    def _substitute_url_prefix(self, url, match_prefix, substitute):
        match_re = r'^{}'.format(re.escape(match_prefix))
        return re.sub(match_re, substitute, url, count=1)

    def _substitute_url_prefixes(self, completion_requirements, property_name, match_prefix, substitute):
        original_urls = completion_requirements.get(property_name, None)
        if original_urls is not None:
            new_urls = [
                self._substitute_url_prefix(badge_url, match_prefix, substitute)
                for badge_url in original_urls
            ]

            if new_urls != original_urls:
                logger.debug('    performed url substitution on "{}" property:\n        original: {},\n        new:      {}'.format(
                    property_name,
                    original_urls,
                    new_urls)
                )

            return new_urls
        else:
            return original_urls

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get('dry_run')
        url_match_prefix = kwargs.get('url_match_prefix')
        url_substitute_prefix = kwargs.get('url_substitute_prefix')

        for pe in PathwayElement.objects.all():
            logger.debug('Processing PathwayElement(pk={})...'.format(pe.pk))

            if pe.completion_requirements is None:
                logger.debug('    completion_requirements is None, skipping'.format(pe.pk))
                continue

            new_badge_urls = self._substitute_url_prefixes(pe.completion_requirements, 'badges', url_match_prefix, url_substitute_prefix)
            if new_badge_urls is not None:
                pe.completion_requirements['badges'] = new_badge_urls

            new_element_urls = self._substitute_url_prefixes(pe.completion_requirements, 'elements', url_match_prefix, url_substitute_prefix)
            if new_element_urls is not None:
                pe.completion_requirements['elements'] = new_element_urls

            if dry_run:
                logger.debug('    PathwayElement(pk={}) save skipped due to --dry-run'.format(pe.pk))
            else:
                pe.save()
                logger.debug('    PathwayElement(pk={}) saved'.format(pe.pk))
