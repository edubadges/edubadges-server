# Created by notto@concentricsky and wiggins@concentricsky.com on 5/25/16.
import itertools
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache

import badgrlog
from issuer.models import BadgeInstance, BadgeClass
from mainsite.celery import app
from recipient.models import RecipientProfile

logger = get_task_logger(__name__)
badgrLogger = badgrlog.BadgrLogger()


@app.task(bind=True)
def award_badges_for_pathway_completion(self, badgeinstance_slug):
    lock_key = "_task_lock_completion_trigger_{}".format(badgeinstance_slug)
    awards = []
    completions = []

    if _acquire_lock(lock_key, self.request.id):
        try:
            # lock acquired

            try:
                badgeinstance = BadgeInstance.cached.get(slug=badgeinstance_slug)
            except BadgeInstance.DoesNotExist:
                return {'status': 'error', 'error': 'BadgeInstance {} not found'.format(badgeinstance_slug)}

            badgeclass = badgeinstance.cached_badgeclass

            recipient_profile = badgeinstance.cached_recipient_profile
            if not recipient_profile:
                return {'status': 'error', 'awards': [], 'error': 'RecipientProfile not found.'}

            completable_elements = badgeclass.cached_pathway_elements()
            pathways = set([ce.cached_pathway for ce in completable_elements])
            if not pathways:
                return {'status': 'done', 'awards': awards}

            completions = list(itertools.chain.from_iterable([recipient_profile.cached_completions(p) for p in pathways]))
            for completion in completions:
                if 'completionBadge' in completion:
                    try:
                        completion_badgeclass = BadgeClass.cached.get(slug=completion.get('completionBadge').get('slug'))
                        try:
                            awarded_badge = BadgeInstance.objects.get(
                                recipient_identifier=recipient_profile.recipient_identifier,
                                badgeclass=completion_badgeclass)
                            # badge was already awarded
                        except BadgeInstance.DoesNotExist:
                            # need to award badge
                            from issuer.serializers import BadgeInstanceSerializer
                            serializer = BadgeInstanceSerializer(data={
                                'recipient_identifier': recipient_profile.recipient_identifier,
                                'create_notification': getattr(settings, 'ISSUER_NOTIFY_DEFAULT', True),
                            })
                            serializer.is_valid(raise_exception=True)
                            new_instance = serializer.save(
                                check_completions=False,
                                issuer=completion_badgeclass.issuer,
                                badgeclass=completion_badgeclass
                            )
                            pass
                    except BadgeClass.DoesNotExist:
                        # got an erroneous badgeclass for a completionBadge
                        pass

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


def _acquire_lock(key, taskId, expiration=60*5):
    return cache.add(key, taskId, expiration)


def _lock_resume(key):
    return cache.get(key)


def _release_lock(key):
    return cache.delete(key)
