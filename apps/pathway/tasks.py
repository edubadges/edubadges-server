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

    if _acquire_lock(lock_key, self.request.id):
        try:
            # lock acquired

            from issuer.serializers import BadgeInstanceSerializer  # avoid circular import
            awards = []
            badgeclass = badgeinstance.cached_badgeclass
            element_triggers = PathwayElementBadge.objects.filter(
                badgeclass=badgeclass).select_related('element')

            if not element_triggers.exists():
                return {'status': 'done', 'awards': awards}

            elements = [et.element for et in element_triggers]

            recipient_profile = RecipientProfile.objects.get(
                recipient_identifier=badgeinstance.recipient_identifier)

            recipient_instances = RecipientProfile.cached_badgeinstances()


            for element in elements:
                awards = awards + _cascade_completion_checks(
                    element, recipient_profile, recipient_instances)


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


def _cascade_completion_checks(element, recipient_profile, recipient_instances):
    awards = []

    if element.recipient_completion(recipient_profile, recipient_instances):

        if element.completion_badgeclass \
                and not _is_badgeclass_awarded(element.completion_badgeclass, recipient_instances):

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
