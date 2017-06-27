import logging
import re
from functools import partial

from django.conf import settings
from django.core.management.base import BaseCommand

from pathway.models import PathwayElement

logger = logging.getLogger('command')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class Command(BaseCommand):
    help = 'Perform prefix substitution of badge URLs in pathway completion requirements'

    unexpected_badge_urls = {}
    unexpected_element_urls = {}

    def add_arguments(self, parser):
        parser.add_argument('--url-match-prefix', required=True, help='Perform substitution on urls matching this prefix')
        parser.add_argument('--url-expected-prefix', required=True, help='Substitute matching urls with this prefix.  Also, flag all final urls not matching this prefix for further investigation')
        parser.add_argument('--dry-run', action='store_true', default=False)

    def _substitute_url_prefix(self, url, match_prefix, substitute):
        match_re = r'^{}'.format(re.escape(match_prefix))
        return re.sub(match_re, substitute, url, count=1)

    def _substitute_url_prefixes(self, completion_requirements, property_name, match_prefix, expected_prefix):
        original_urls = completion_requirements.get(property_name, None)
        if original_urls is not None:
            new_urls = [
                self._substitute_url_prefix(badge_url, match_prefix, expected_prefix)
                for badge_url in original_urls
            ]

            urls_changed = (new_urls != original_urls)

            if urls_changed:
                logger.debug('    performed url substitution in "{}":\n        original: {},\n        new:      {}'.format(
                    property_name,
                    original_urls,
                    new_urls)
                )

            return new_urls, urls_changed
        else:
            return original_urls, False

    def _unexpected_url_prefix(self, url, expected_prefix):
        expected_re = r'^{}'.format(re.escape(expected_prefix))
        return re.match(expected_re, url) is None

    def _get_unexpected_urls(self, completion_requirements, property_name, expected_prefix):
        logger.debug('    verifying url prefixes in "{}"'.format(property_name))
        urls = completion_requirements.get(property_name, None)

        if urls is not None:
            non_matching_urls = filter(lambda url: self._unexpected_url_prefix(url, expected_prefix), urls)
            return non_matching_urls
        else:
            return []

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get('dry_run')
        url_match_prefix = kwargs.get('url_match_prefix')
        url_expected_prefix = kwargs.get('url_expected_prefix')

        for pe in PathwayElement.objects.all():
            logger.debug('Processing PathwayElement(pk={})...'.format(pe.pk))

            if pe.completion_requirements is None:
                logger.debug('    completion_requirements is None, skipping'.format(pe.pk))
                continue

            new_badge_urls, badge_urls_changed = self._substitute_url_prefixes(pe.completion_requirements, 'badges', url_match_prefix, url_expected_prefix)
            if badge_urls_changed:
                pe.completion_requirements['badges'] = new_badge_urls

            new_element_urls, element_urls_changed = self._substitute_url_prefixes(pe.completion_requirements, 'elements', url_match_prefix, url_expected_prefix)
            if element_urls_changed:
                pe.completion_requirements['elements'] = new_element_urls

            if badge_urls_changed or element_urls_changed:
                logger.debug('    saving PathwayElement(pk={})...'.format(pe.pk))
                if not dry_run:
                    pe.save()
                    logger.debug('    done')
                else:
                    logger.debug('    (skipped due to --dry-run)')
            else:
                logger.debug('    no url changes, skipping save')

            unexpected_badge_urls = self._get_unexpected_urls(pe.completion_requirements, 'badges', url_expected_prefix)
            if len(unexpected_badge_urls) > 0:
                logger.debug('        found unexpected urls: {}'.format(unexpected_badge_urls))
                self.unexpected_badge_urls[pe.pk] = unexpected_badge_urls

            unexpected_element_urls = self._get_unexpected_urls(pe.completion_requirements, 'elements', url_expected_prefix)
            if len(unexpected_element_urls) > 0:
                logger.debug('        found unexpected urls: {}'.format(unexpected_element_urls))
                self.unexpected_element_urls[pe.pk] = unexpected_element_urls


        logger.debug('UNEXPECTED BADGE URLs (pk, urls):')

        for pk, urls in self.unexpected_badge_urls.items():
            logger.debug('    {}, {}'.format(pk, urls))

        logger.debug('UNEXPECTED ELEMENT URLs (pk, urls):')
        for pk, urls in self.unexpected_element_urls.items():
            logger.debug('    {}, {}'.format(pk, urls))
