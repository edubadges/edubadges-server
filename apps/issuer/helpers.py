# encoding: utf-8


import uuid
from collections import MutableMapping

import openbadges
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from issuer.models import Issuer, BadgeClass, BadgeInstance
from mainsite.utils import first_node_match
from requests_cache.backends import BaseCache


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
        query = [v for v in query if v is not None]
        if len(query) != 1:
            raise ValueError("Must provide only 1 of: url, imagefile or assertion_obo")
        query = query[0]

        if created_by:
            recipient_id = created_by.get_recipient_identifier(),        
            badgecheck_recipient_profile = {
                'id': created_by.get_recipient_identifier(),
                'email': [email.email for email in created_by.verified_emails]
            }
        else:
            badgecheck_recipient_profile = None

        try:
            response = openbadges.verify(query, recipient_profile=badgecheck_recipient_profile, **cls.badgecheck_options())
        except ValueError as e:
            raise ValidationError([{'name': "INVALID_BADGE", 'description': str(e)}])

        report = response.get('report', {})
        # override VALIDATE_PROPERTY for id, until IMS accepts EduID iri format 
                
        if report['errorCount'] > 0:
            index_of_uri_format_failure = None
            uri_format_message_found = False
            for index, message in enumerate(report['messages']):
                if 'not valid in unknown type node' in message['result']:
                    index_of_uri_format_failure = index
                    uri_format_message_found = True
            if uri_format_message_found:
                report['errorCount'] -= 1
                report['messages'].pop(index_of_uri_format_failure)
                if report['errorCount'] == 0:
                    report['valid'] = True
        

        is_valid = report.get('valid')

        if not is_valid:
            if report.get('errorCount', 0) > 0:
                errors = list(cls.translate_errors(report.get('messages', [])))
            else:
                errors = [{'name': "UNABLE_TO_VERIFY", 'description': "Unable to verify the assertion"}]
            raise ValidationError(errors)

        graph = response.get('graph', [])

        assertion_obo = first_node_match(graph, dict(type="Assertion"))
        if not assertion_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find an assertion"}])

        badgeclass_obo = first_node_match(graph, dict(id=assertion_obo.get('badge', None)))
        if not badgeclass_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find a badgeclass"}])

        issuer_obo = first_node_match(graph, dict(id=badgeclass_obo.get('issuer', None)))
        if not issuer_obo:
            raise ValidationError([{'name': "ASSERTION_NOT_FOUND", 'description': "Unable to find an issuer"}])

        original_json = response.get('input').get('original_json', {})

        recipient_identifier = report.get('recipientProfile', {}).get('id', None) # first use 'id' as the recipient_identifier type
        if not recipient_identifier: # the assertion might instead have the 'email' recipient_identifier type
            recipient_identifier = report.get('recipientProfile', {}).get('email', None) 

        with transaction.atomic():
            issuer, issuer_created = Issuer.objects.get_or_create_from_ob2(issuer_obo, original_json=original_json.get(issuer_obo.get('id')))
            badgeclass, badgeclass_created = BadgeClass.objects.get_or_create_from_ob2(issuer, badgeclass_obo, original_json=original_json.get(badgeclass_obo.get('id')))
            return BadgeInstance.objects.get_or_create_from_ob2(badgeclass, assertion_obo, recipient_identifier=recipient_identifier, original_json=original_json.get(assertion_obo.get('id')))

    @classmethod
    def get_assertion_obo(cls, badge_instance):
        try:
            response = openbadges.verify(badge_instance.source_url, recipient_profile=None, **cls.badgecheck_options())
        except ValueError as e:
            return None

        report = response.get('report', {})
        is_valid = report.get('valid')

        if is_valid:
            graph = response.get('graph', [])

            assertion_obo = first_node_match(graph, dict(type="Assertion"))
            if assertion_obo:
                return assertion_obo
