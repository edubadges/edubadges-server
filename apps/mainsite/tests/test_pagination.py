import json
from urllib.parse import urlencode

from django.test import TransactionTestCase
from django_mock_queries.query import MockSet, MockModel
from mainsite.pagination import EncryptedCursorPagination
from rest_framework.renderers import JSONRenderer
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory


class DecryptedCursorPagination(EncryptedCursorPagination):
    ordering = 'pk'
    encrypt = False  # Assist with test cases
    page_size = 3


class TestEncryptedCursorPagination(TransactionTestCase):
    request_factory = APIRequestFactory()

    def setUp(self):
        self.paginator = DecryptedCursorPagination()

    def _mock_get_request(self, url):
        return Request(self.request_factory.get(url))

    @staticmethod
    def _get_pks(page):
        return [int(e.pk) for e in page]

    def _do_paginate_queryset_asserts(self, url, queryset_pks, expected_pks,
                                      has_prev, prev_cursor,
                                      has_next, next_cursor):

        self.paginator = DecryptedCursorPagination()
        queryset = MockSet(*[MockModel(pk=str(pk)) for pk in queryset_pks])

        # Useful for debugging tests:
        #
        # print('TEST CASE: '
        #      'url="{}" queryset_pks="{}", expected_pks="{}", '
        #      'has_prev="{}", prev_cursor="{}", '
        #      'has_next="{}", next_cursor="{}"'.format(url, queryset_pks, expected_pks,
        #                                               has_prev, prev_cursor,
        #                                               has_next, next_cursor))

        page = self.paginator.paginate_queryset(queryset, self._mock_get_request(url))

        self.assertEqual(self._get_pks(page), expected_pks)

        self.assertEqual(self.paginator.has_prev, has_prev)
        self.assertEqual(self.paginator.prev_cursor, prev_cursor)
        prev_link = 'http://testserver/?{}'.format(urlencode({'cursor': prev_cursor})) if prev_cursor is not None else prev_cursor
        self.assertEqual(self.paginator.prev_link, prev_link)

        self.assertEqual(self.paginator.has_next, has_next)
        self.assertEqual(self.paginator.next_cursor, next_cursor)
        next_link = 'http://testserver/?{}'.format(urlencode({'cursor': next_cursor})) if next_cursor is not None else next_cursor
        self.assertEqual(self.paginator.next_link, next_link)

    #@unittest.skip('For debug speedup')
    def test_paginate_malformed_cursor_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.paginator.paginate_queryset(MockSet(), self._mock_get_request('/?cursor=foo'))

        with self.assertRaises(ValueError):
            self.paginator.paginate_queryset(MockSet(), self._mock_get_request('/?cursor=foo:bar'))

    #@unittest.skip('For debug speedup')
    def test_paginate_disjoint(self):
        test_cases = [
            # url           input        output    has_prev  prev_cursor  has_next  next_cursor
            ####################################################################################
            ('/?cursor=:0', [1,2,3,4,5], [],       False,    None,        False,        None),
            ('/?cursor=:1', [1,2,3,4,5], [],       False,    None,        False,        None),
            ('/?cursor=5:', [1,2,3,4,5], [],       False,    None,        False,        None),
            ('/?cursor=6:', [1,2,3,4,5], [],       False,    None,        False,        None),
            ('/?cursor=7:', [1,2,3,4,5], [],       False,    None,        False,        None)]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_paginate_left_aligned(self):
        test_cases = [
            # url           input        output    has_prev  prev_cursor  has_next  next_cursor
            ####################################################################################
            ('/',           [1,2,3,4,5], [1,2,3],  False,    ':1',        True,        '3:'),
            ('/?cursor=0:', [1,2,3,4,5], [1,2,3],  False,    ':1',        True,        '3:'),
            ('/?cursor=:4', [1,2,3,4,5], [1,2,3],  False,    ':1',        True,        '3:')]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_paginate_right_aligned(self):
        test_cases = [
            # url           input        output   has_prev  prev_cursor  has_next  next_cursor
            ###################################################################################
            ('/?cursor=2:', [1,2,3,4,5], [3,4,5], True,     ':3',        False,    '5:'),
            ('/?cursor=:6', [1,2,3,4,5], [3,4,5], True,     ':3',        False,    '5:')]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_paginate_both_aligned(self):
        test_cases = [
            # url           input        output    has_prev  prev_cursor  has_next  next_cursor
            ##################################################################################
            ('/',           [1,2,3],     [1,2,3],  False,    ':1',       False,     '3:'),
            ('/?cursor=0:', [1,2,3],     [1,2,3],  False,    ':1',       False,     '3:'),
            ('/?cursor=:4', [1,2,3],     [1,2,3],  False,    ':1',       False,     '3:')]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_paginate_middle_aligned(self):
        test_cases = [
            # url           input         output     has_prev  prev_cursor  has_next  next_cursor
            #####################################################################################
            ('/?cursor=1:', [1,2,3,4,5],  [2,3,4],   True,    ':2',        True,     '4:'),
            ('/?cursor=:5', [1,2,3,4,5],  [2,3,4],   True,    ':2',        True,     '4:')]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_paginate_undersized(self):
        test_cases = [
            # url            input   output     has_prev  prev_cursor  has_next  next_cursor
            ######################################################################################
            ('/',            [],      [],       False,     None,       False,     None),
            ('/?cursor=1:',  [],      [],       False,     None,       False,     None),
            ('/?cursor=:1',  [],      [],       False,     None,       False,     None),
            ('/',            [1,2],   [1,2],    False,     ":1",       False,     "2:"),
            ('/?cursor=0:',  [1,2],   [1,2],    False,     ":1",       False,     "2:"),
            ('/?cursor=1:',  [1,2],   [2],      True,      ":2",       False,     "2:"),
            ('/?cursor=:2',  [1,2],   [1],      False,     ":1",       True,      "1:")]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_missing_cursor_key(self):
        test_cases = [
            # url           input        output    has_prev  prev_cursor  has_next  next_cursor
            ####################################################################################
            ('/?cursor=2:', [1,3,4,5],   [3,4,5],  True,     ':3',        False,        '5:'),
            ('/?cursor=:4', [1,2,3,5],   [1,2,3],  False,    ':1',        True,         '3:')]

        for args in test_cases:
            self._do_paginate_queryset_asserts(*args)

    #@unittest.skip('For debug speedup')
    def test_get_paginated_response(self):
        self.paginator.next_link = 'aaa'
        self.paginator.has_next = 'bbb'
        self.paginator.next_cursor = 'ccc'

        self.paginator.prev_link = 'ddd'
        self.paginator.has_prev = 'eee'
        self.paginator.prev_cursor = 'fff'

        response = self.paginator.get_paginated_response('ggg')

        self.assertEqual(response.status_code, 200)

        response_body = json.loads(JSONRenderer().render(response.data))
        self.assertEqual(response_body, {"nextResults": "aaa",
                                         "hasNext": "bbb",
                                         "nextCursor": "ccc",
                                         "previousResults": "ddd",
                                         "hasPrevious": "eee",
                                         "previousCursor": "fff",
                                         "results": "ggg"})