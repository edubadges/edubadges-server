import json

import responses

from django.test import TestCase

from integrity_verifier import *
from .testfiles.test_components import test_components


class InstanceVerificationTests(TestCase):

    @responses.activate
    def test_1_0_minimal(self):
        responses.add(
            responses.GET, 'http://a.com/instance',
            body=test_components['basic_instance'],
            status=200, content_type='application/json'
        )
        responses.add(
            responses.GET, 'http://a.com/badgeclass',
            body=test_components['basic_badgeclass'],
            status=200, content_type='application/json'
        )
        responses.add(
            responses.GET, 'http://a.com/issuer',
            body=test_components['basic_issuer'],
            status=200, content_type='application/json'
        )

        rbi = RemoteBadgeInstance('http://a.com/instance')
        abi = AnalyzedBadgeInstance(rbi, recipient_id='a@b.com')
