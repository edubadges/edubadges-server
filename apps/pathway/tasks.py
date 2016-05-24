# Created by wiggins@concentricsky.com on 7/30/15.
import StringIO
import csv
import itertools
import time
from allauth.account.adapter import get_adapter

from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache

import badgrlog
from mainsite.celery import app
from pathway.models import PathwayElement, PathwayElementBadge
from recipient.models import RecipientProfile

logger = get_task_logger(__name__)
badgrLogger = badgrlog.BadgrLogger()


@app.task(bind=True)
def check_element_completions_triggered_by_badge_award(badgeinstance):
    lock_key = "_task_lock_completion_trigger_{}{}".format(
        badgeinstance.slug, badgeinstance.recipient_identifier)
    awards = []
    completions = []

    if _acquire_lock(lock_key, self.request.id):
        try:
            # lock acquired

            from issuer.serializers import BadgeInstanceSerializer  # avoid circular import
            badgeclass = badgeinstance.cached_badgeclass
            completable_elements = badgeclass.cached_pathway_elements()

            if not completable_elements:
                return {'status': 'done', 'awards': awards}

            pathways = set([ce.element.pathway for ce in completable_elements])

            try:
                recipient_profile = RecipientProfile.objects.get(
                    recipient_identifier=badgeinstance.recipient_identifier)
            except RecipientProfile.DoesNotExist:
                return {'status': 'error', 'awards': [], 'error': 'RecipientProfile not found.'}


            for pathway in pathways:
                completions = completions + recipient_profile.cached_completions(pathway)


        finally:
            _release_lock(lock_key)

        return {
            'status': 'done',
            'awards': awards
        }
    return {
        'locked': True,
        'resume': _lock_resume(lock_key)
    }


@app.task(bind=True)
def award_completion_badge(element, recipient_profile):

    if element.recipient_completion(recipient_profile, recipient_instances):

        if element.completion_badgeclass \
                and not _is_badgeclass_awarded(element.completion_badgeclass, recipient_instances):

            if element.is_completed_by(recipient_profile, recipient_instances):

                element_subtree = element.pathway.build_element_tree(element)

                from issuer.serializers import BadgeInstanceSerializer

                # new_instance = Award completion badgeclass
                data = {
                    'recipient_identifier': recipient_profile.recipient_identifier,
                    'create_notification': getattr(settings, 'ISSUER_NOTIFY_DEFAULT', True),
                    'badgeclass': element.completion_badgeclass
                }

                logger.info("Awarding element badge {}\n".format(data))

                serializer = BadgeInstanceSerializer(data=data)
                serializer.is_valid(raise_exception=True)
                new_instance = serializer.save()

                recipient_instances = recipient_profile.cached_badgeinstances()
                awards.append(new_instance)

        if element.parent_element:
            return awards + _cascade_completion_checks(
                element.parent_element, recipient_profile, recipient_instances)

    return awards

def _is_badgeclass_awarded(badgeclass, instances):
    for instance in instances:
        if instance.badgeclass == badgeclass:
            return True
    return False


def _acquire_lock(key, taskId, expiration=60*5):
    return cache.add(key, taskId, expiration)


def _lock_resume(key):
    return cache.get(key)


def _release_lock(key):
    return cache.delete(key)
