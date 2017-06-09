# encoding: utf-8
from __future__ import unicode_literals

import badgecheck
from django.core.exceptions import ValidationError
from django.db import transaction

from issuer.models import Issuer, BadgeClass, BadgeInstance


class BadgeCheckHelper(object):

    @classmethod
    def get_or_create_assertion(cls, url=None, imagefile=None, assertion_obo=None):
        # distill 3 optional arguments into one query argument
        query = (url, imagefile, assertion_obo)
        query = filter(lambda v: v is not None, query)
        if len(query) != 1:
            raise ValueError("Must provide only 1 of: url, imagefile or assertion_obo")
        query = query[0]

        response = badgecheck.verify(query)
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

        with transaction.atomic():
            issuer, issuer_created = Issuer.objects.get_or_create_from_ob2(obos.get('Issuer'))
            badgeclass, badgeclass_created = BadgeClass.objects.get_or_create_from_ob2(issuer, obos.get('BadgeClass'))
            return BadgeInstance.objects.get_or_create_from_ob2(badgeclass, obos.get('Assertion'))







