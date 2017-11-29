import logging
import re
from urlparse import urlparse

from collections import defaultdict
from django.core.exceptions import FieldError
from django.core.management.base import BaseCommand
from django.core.urlresolvers import resolve

from issuer.models import BadgeClass
from pathway.models import PathwayElement, PathwayElementBadge

logger = logging.getLogger('command')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


class Command(BaseCommand):
    help = 'Resolve BadgeClass slug URLs to entity ID URLs'

    unrecognized_badge_urls = defaultdict(list)
    unrecognized_element_urls = defaultdict(list)

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', default=False)

    def _resolve_entity_id_url(self, url, pk, model=BadgeClass):
        # import pdb; pdb.set_trace();
        parsed = urlparse(url)
        resolved = resolve(parsed.path)

        entity_id = resolved.kwargs.get('entity_id', resolved.kwargs.get('element_slug'))
        try:
            bc = model.objects.get(entity_id=entity_id)
            path = bc.get_absolute_url()
            return (parsed._replace(path=path).geturl(), bc,)
        except (FieldError, model.DoesNotExist):
            pass

        try:
            el = model.objects.get(slug=entity_id)
            path = urlparse(el.jsonld_id).path
            return (parsed._replace(path=path).geturl(), el,)
        except BadgeClass.DoesNotExist:
            # Unable to resolve badge, do no modify and log for further analysis
            self.unrecognized_badge_urls[pk].append(url)
            return (url, None,)
        except PathwayElement.DoesNotExist:
            # Unable to resolve element, do no modify and log for further analysis
            self.unrecognized_element_urls[pk].append(url)
            return (url, None,)

    def _resolve_entity_id_urls(self, pe, property_name, model=BadgeClass):
        completion_requirements = pe.completion_requirements
        original_urls = completion_requirements.get(property_name, None)
        if original_urls is not None:

            new_urls = [
                self._resolve_entity_id_url(url, pe.pk, model=model)  # tuple(url, model_instance)
                for url in original_urls
            ]

            urls_changed = ([u[0] for u in new_urls] != original_urls)

            if urls_changed:
                logger.debug('    performed url substitution in "{}":\n        original: {},\n        new:      {}'.format(
                    property_name,
                    original_urls,
                    new_urls)
                )

            return new_urls, urls_changed
        else:
            return original_urls, False

    def handle(self, *args, **kwargs):
        dry_run = kwargs.get('dry_run')

        pe_count = PathwayElement.objects.count()

        n = 0
        badge_updates = 0
        element_updates = 0
        for pe in PathwayElement.objects.all():
            n += 1
            logger.debug('({}/{}) Processing PathwayElement(pk={})...'.format(n, pe_count, pe.pk))

            if pe.completion_requirements is None:
                logger.debug('    completion_requirements is None, skipping'.format(pe.pk))
                continue

            new_badges, badge_urls_changed = self._resolve_entity_id_urls(pe, 'badges')
            if new_badges is None:
                new_badges = []
            badges = [u[1] for u in new_badges]
            current_badges = pe.cached_badges()
            if badge_urls_changed or set(badges) != set(current_badges):
                badge_updates += 1
                pe.completion_requirements['badges'] = [u[0] for u in new_badges]
                for peb in current_badges:
                    if peb not in badges:
                        logger.debug('    Adding Badge {} to Element {} badge set.'.format(peb.badgeclass.entity_id, pe.slug))
                        if not dry_run:
                            peb.delete()
                for b in badges:
                    if b not in current_badges and b is not None:
                        logger.debug('    Removing Badge {} from Element {} badge set.'.format(b.entity_id, pe.slug))
                        if not dry_run:
                            PathwayElementBadge.objects.create(badgeclass=b, element=pe, pathway=pe.pathway)

            new_elements, element_urls_changed = self._resolve_entity_id_urls(pe, 'elements', model=PathwayElement)
            if new_elements is None:
                new_elements = []
            current_children = pe.cached_children()
            elements = [e[1] for e in new_elements]
            if element_urls_changed or not all([ee in current_children for ee in elements]):
                element_updates += 1
                pe.completion_requirements['elements'] = [e[0] for e in new_elements]
                for e in elements:
                    if e not in current_children:
                        logger.debug('    Adding Element {} to Element {} children set.'.format(e.slug, pe.slug))
                        if not dry_run:
                            pe.pathwayelement_set.add(e)
            if badge_urls_changed or element_urls_changed:
                logger.debug('    saving PathwayElement(pk={})...'.format(pe.pk))
                if not dry_run:
                    pe.save(update_badges=False)
                    logger.debug('    done')
                else:
                    logger.debug('    (skipped due to --dry-run)')
            else:
                logger.debug('    no url changes, skipping save')

        logger.debug('UNRECOGNIZED BADGE URLs (pk, urls):')
        for pk, urls in self.unrecognized_badge_urls.items():
            logger.debug('    {}, {}'.format(pk, urls))
        logger.debug('UNRECOGNIZED ELEMENT URLs (pk, urls):')
        for pk, urls in self.unrecognized_element_urls.items():
            logger.debug('    {}, {}'.format(pk, urls))

        logger.debug('Badge updates: {}, Element updates: {}'.format(badge_updates, element_updates))
