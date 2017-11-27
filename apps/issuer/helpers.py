# encoding: utf-8
from __future__ import unicode_literals

import uuid
from collections import MutableMapping

import openbadges
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from requests_cache.backends import RedisCache, BaseCache

from issuer.models import Issuer, BadgeClass, BadgeInstance


# TODO: Fix this class, its broken!
class DjangoCacheDict(MutableMapping):
    _keymap_cache_key = "DjangoCacheDict_keys"

    def __init__(self, namespace, id=None, timeout=None):
        self.namespace = namespace
        self._timeout = timeout

        if id is None:
            id = uuid.uuid4().hexdigest()
        self._id = id
        self.keymap_cache_key = self._keymap_cache_key+"_"+self._id

    def build_key(self, *args):
        return "{keymap_cache_key}{namespace}{key}".format(
            keymap_cache_key=self.keymap_cache_key,
            namespace=self.namespace,
            key="".join(args)
        ).encode("utf-8")

    def timeout(self):
        return self._timeout

    def _keymap(self):
        keymap = cache.get(self.keymap_cache_key)
        if keymap is None:
            return []
        return keymap

    def __getitem__(self, key):
        result = cache.get(self.build_key(key))
        if result is None:
            raise KeyError
        return result

    def __setitem__(self, key, value):
        built_key = self.build_key(key)
        cache.set(built_key, value, timeout=self.timeout())

        # this probably needs locking...
        keymap = self._keymap()
        keymap.append(built_key)
        cache.set(self.keymap_cache_key, keymap, timeout=None)

    def __delitem__(self, key):
        built_key = self.build_key(key)
        cache.delete(built_key)

        # this probably needs locking...
        keymap = self._keymap()
        keymap.remove(built_key)
        cache.set(self.keymap_cache_key, keymap, timeout=None)

    def __len__(self):
        keymap = self._keymap()
        return len(keymap)

    def __iter__(self):
        keymap = self._keymap()
        for key in keymap:
            yield cache.get(key)

    def __str__(self):
        return '<{}>'.format(self.keymap_cache_key)

    def clear(self):
        self._id = uuid.uuid4().hexdigest()
        self.keymap_cache_key = self._keymap_cache_key+"_"+self._id


class DjangoCacheRequestsCacheBackend(BaseCache):
    def __init__(self, namespace='requests-cache', **options):
        super(DjangoCacheRequestsCacheBackend, self).__init__(**options)
        self.responses = DjangoCacheDict(namespace, 'responses')
        self.keys_map = DjangoCacheDict(namespace, 'urls')


class BadgeCheckHelper(object):
    _cache_instance = None
    error_map = [
        (['FETCH_HTTP_NODE'], {
            'name': "FETCH_HTTP_NODE",
            'description': "Unable to reach URL",
        }),
        (['VERIFY_RECIPIENT_IDENTIFIER'], {
            'name': 'VERIFY_RECIPIENT_IDENTIFIER',
            'description': "The recipient does not match any of your verified emails",
        }),
        (['VERIFY_JWS', 'VERIFY_KEY_OWNERSHIP'], {
            'name': "VERIFY_SIGNATURE",
            "description": "Could not verify signature",
        }),
        (['VERIFY_SIGNED_ASSERTION_NOT_REVOKED'], {
            'name': "ASSERTION_REVOKED",
            "description": "This assertion has been revoked",
        }),
    ]

    @classmethod
    def translate_errors(cls, badgecheck_messages):
        for m in badgecheck_messages:
            if m.get('messageLevel') == 'ERROR':
                for errors, backpack_error in cls.error_map:
                    if m.get('name') in errors:
                        yield backpack_error
                yield m

    @classmethod
    def cache_instance(cls):
        if cls._cache_instance is None:
            # TODO: note this class is broken and does not work correctly!
            cls._cache_instance = DjangoCacheRequestsCacheBackend(namespace='badgr_requests_cache')
        return cls._cache_instance

    @classmethod
    def badgecheck_options(cls):
        return getattr(settings, 'BADGECHECK_OPTIONS', {
            'include_original_json': True,
            'use_cache': True,
            # 'cache_backend': cls.cache_instance()  #  just use locmem cache for now 
        })

    @classmethod
    def get_or_create_assertion(cls, url=None, imagefile=None, assertion=None, created_by=None):

        # distill 3 optional arguments into one query argument
        query = (url, imagefile, assertion)
        query = filter(lambda v: v is not None, query)
        if len(query) != 1:
            raise ValueError("Must provide only 1 of: url, imagefile or assertion_obo")
        query = query[0]

        if created_by:
            badgecheck_recipient_profile = {
                'email': created_by.all_recipient_identifiers
            }
        else:
            badgecheck_recipient_profile = None

        try:
            response = openbadges.verify(query, recipient_profile=badgecheck_recipient_profile, **cls.badgecheck_options())
        except ValueError as e:
            raise ValidationError([{'name': "INVALID_BADGE", 'description': str(e)}])

        report = response.get('report', {})
        is_valid = report.get('valid')

        if not is_valid:
            if report.get('errorCount', 0) > 0:
                errors = list(cls.translate_errors(report.get('messages', [])))
            else:
                errors = [{'name': "UNABLE_TO_VERIFY", 'description': "Unable to verify the assertion"}]
            raise ValidationError(errors)

        def _first_node_match(graph, condition):
            """return the first dict in a list of dicts that matches condition dict"""
            for node in graph:
                if all(item in node.items() for item in condition.items()):
                    return node

        graph = response.get('graph', [])

        assertion_obo = _first_node_match(graph, dict(type="Assertion"))
        if not assertion_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find an assertion"}])

        badgeclass_obo = _first_node_match(graph, dict(id=assertion_obo.get('badge', None)))
        if not badgeclass_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find a badgeclass"}])

        issuer_obo = _first_node_match(graph, dict(id=badgeclass_obo.get('issuer', None)))
        if not issuer_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find an issuer"}])

        original_json = response.get('input').get('original_json', {})

        recipient_identifier = report.get('recipientProfile', {}).get('email', None)

        with transaction.atomic():
            issuer, issuer_created = Issuer.objects.get_or_create_from_ob2(issuer_obo, original_json=original_json.get(issuer_obo.get('id')))
            badgeclass, badgeclass_created = BadgeClass.objects.get_or_create_from_ob2(issuer, badgeclass_obo, original_json=original_json.get(badgeclass_obo.get('id')))
            return BadgeInstance.objects.get_or_create_from_ob2(badgeclass, assertion_obo, recipient_identifier=recipient_identifier, original_json=original_json.get(assertion_obo.get('id')))







