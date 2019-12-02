# Created by notto@concentricsky and wiggins@concentricsky.com on 5/25/16.
import itertools
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError

import badgrlog
from mainsite.celery import app


logger = get_task_logger(__name__)
badgrLogger = badgrlog.BadgrLogger()

pathways_task_queue_name = getattr(settings, 'PATHWAYS_TASK_QUEUE_NAME', 'default')


@app.task(bind=True, queue=pathways_task_queue_name)
def award_badges_for_pathway_completion(self, badgeinstance_pk):
    from issuer.models import BadgeInstance, BadgeClass

    lock_key = "_task_lock_completion_trigger_{}".format(badgeinstance_pk)
    awards = []
    completions = []

    if _acquire_lock(lock_key, self.request.id):
        try:
            # lock acquired

            try:
                badgeinstance = BadgeInstance.cached.get(pk=badgeinstance_pk)
            except BadgeInstance.DoesNotExist:
                return {'status': 'error', 'error': 'BadgeInstance {} not found'.format(badgeinstance_pk)}

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
                completion_badgeclass = None
                if 'element' in completion and hasattr(completion['element'], 'completion_badgeclass'):
                    completion_badgeclass = completion['element'].completion_badgeclass
                elif 'completionBadge' in completion:
                    try:
                        completion_badgeclass = BadgeClass.cached.get(entity_id=completion.get('completionBadge').get('slug'))
                    except BadgeClass.DoesNotExist:
                        # got an erroneous badgeclass for a completionBadge
                        pass
                    
                if completion_badgeclass:
                    try:
                        awarded_badge = BadgeInstance.objects.get(
                            recipient_identifier=recipient_profile.recipient_identifier,
                            badgeclass=completion_badgeclass)
                        # badge was already awarded
                    except BadgeInstance.DoesNotExist:
                        # need to award badge
                        awarded_badge = completion_badgeclass.issue(
                            recipient_profile.recipient_identifier,
                            notify=getattr(settings, 'ISSUER_NOTIFY_DEFAULT', True),
                            created_by=None
                        )
                    awards.append(awarded_badge)

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


@app.task(queue=pathways_task_queue_name)
def resave_all_elements():
    from pathway.models import PathwayElement
    for el in PathwayElement.objects.all():
        try:
            el.save(update_badges=True)
        except ValidationError as e:
            print(("ERROR on {}: {}".format(el.pk, e.message)))
            pass


def _acquire_lock(key, taskId, expiration=60*5):
    return cache.add(key, taskId, expiration)


def _lock_resume(key):
    return cache.get(key)


def _release_lock(key):
    return cache.delete(key)