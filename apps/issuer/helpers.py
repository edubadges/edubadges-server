# encoding: utf-8
from __future__ import unicode_literals

import badgecheck
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from issuer.models import Issuer, BadgeClass, BadgeInstance


class BadgeCheckHelper(object):
    @classmethod
    def badgecheck_options(cls):
        return getattr(settings, 'BADGECHECK_OPTIONS', {
            'include_original_json': True
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

        response = badgecheck.verify(query, recipient_profile=badgecheck_recipient_profile, options=cls.badgecheck_options())
        is_valid = response.get('valid')

        # we expect to get 3 obos: Assertion, Issuer and BadgeClass
        obos = {n.get('type'): n for n in response.get('graph', [])}
        if len(set(('Assertion', 'Issuer', 'BadgeClass')) & set(obos.keys())) != 3:
            is_valid = False

        if not is_valid:
            errors = []
            if response.get('errorCount', 0) > 0:
                errors = filter(lambda m: m.get('messageLevel') == 'ERROR', response.get('messages'))
            else:
                errors = [{'name': "UNABLE_TO_VERIFY", 'description': "Unable to verify the assertion"}]
            raise ValidationError(errors)

        issuer_obo = obos.get('Issuer')
        badgeclass_obo = obos.get('BadgeClass')
        assertion_obo = obos.get('Assertion')
        original_json = response.get('input').get('original_json', {})

        with transaction.atomic():
            issuer, issuer_created = Issuer.objects.get_or_create_from_ob2(issuer_obo, original_json=original_json.get(issuer_obo.get('id')))
            badgeclass, badgeclass_created = BadgeClass.objects.get_or_create_from_ob2(issuer, badgeclass_obo, original_json=original_json.get(badgeclass_obo.get('id')))
            return BadgeInstance.objects.get_or_create_from_ob2(badgeclass, assertion_obo, original_json=original_json.get(assertion_obo.get('id')))







