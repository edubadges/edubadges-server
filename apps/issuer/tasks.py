# encoding: utf-8
from __future__ import unicode_literals

import json

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from requests import ConnectionError
import openbadges_bakery

import badgrlog
from issuer.models import BadgeClass, BadgeInstance
from issuer.utils import CURRENT_OBI_VERSION
from mainsite.celery import app

logger = get_task_logger(__name__)
badgrLogger = badgrlog.BadgrLogger()


@app.task(bind=True, autoretry_for=(ConnectionError,), retry_backoff=True, max_retries=10)
def notify_badgerank_of_badgeclass(self, badgeclass_pk):
    badgerank_enabled = getattr(settings, 'BADGERANK_NOTIFY_ENABLED', True)
    if not badgerank_enabled:
        return {
            'success': True,
            'message': "skipping since BADGERANK_NOTIFY_ENABLED=False"
        }

    try:
        badgeclass = BadgeClass.cached.get(pk=badgeclass_pk)
    except BadgeClass.DoesNotExist:
        return {
            'success': False,
            'error': "Unknown badgeclass pk={}".format(badgeclass_pk)
        }

    badgerank_notify_url = getattr(settings, 'BADGERANK_NOTIFY_URL', 'https://api.badgerank.org/v1/badgeclass/submit')
    response = requests.post(badgerank_notify_url, json=dict(url=badgeclass.public_url))
    if response.status_code != 200:
        return {
            'success': False,
            'status_code': response.status_code,
            'response': response.content
        }
    return {
        'success': True
    }


@app.task(bind=True)
def rebake_assertion_image(self, assertion_entity_id=None, obi_version=CURRENT_OBI_VERSION):

    try:
        assertion = BadgeInstance.cached.get(entity_id=assertion_entity_id)
    except BadgeInstance.DoesNotExist as e:
        return {
            'success': False,
            'error': "Unknown assertion entity_id={}".format(assertion_entity_id)
        }

    assertion.rebake(obi_version=obi_version)

    return {
        'success': True
    }
