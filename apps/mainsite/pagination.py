import more_itertools

from cryptography.fernet import Fernet

from django.conf import settings
from django.db import transaction

from rest_framework.compat import OrderedDict
from rest_framework.pagination import BasePagination
from rest_framework.response import Response
from rest_framework.utils.urls import replace_query_param


class EncryptedCursorPagination(BasePagination):
    """
    Performs cursor-based pagination of QuerySets with support for Fernet-based [1] symmetrical encryption of cursors.
    Implements standard Django REST framework pagination API [2].

    PIP Requirements:
      * cryptography
      * more_itertools

    Usage:
      * Ordering field (default: 'pk') of model to be paginated must be unique, not null, and monotonically increasing
      * Add PAGINATION_SECRET_KEY to settings.py.  Must be base64-encoded 32 byte random string [1].  For example:
        python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key())"

    [1] https://cryptography.io/en/latest/fernet/
    [2] http://www.django-rest-framework.org/api-guide/pagination/

    To change paginator settings, inherit from EncryptedCursorPagination and override the settings.  For example:

    class LargeEncryptedCursorPagination(EncryptedCursorPagination):
        page_size = 100

    RECOMMENDED USE CASE #1:

    class ExampleAPI(BaseAPIView):
        pagination_class = EncryptedCursorPagination

        def get(self, request, *params):
            # ... Initialize queryset

            paginator = self.pagination_class()
            page = paginator.paginate_queryset(queryset, request)
            serializer = ExampleSerializer(page, many=True, context={'request': request})
            return paginator.get_paginated_response(serializer.data)

    RECOMMENDED USE CASE #2:

    class ExampleListView(ListAPIView):
        queryset = ExampleModel.objects.all()
        pagination_class = EncryptedCursorPagination
        serializer_class = ExampleSerializer

        def get_queryset(self)
            # Return un-paginated queryset.  Pagination performed automagically.

    EXAMPLE REQUESTS:

      GET https://example.com/apiEndpoint HTTP/1.1
      GET https://example.com/apiEndpoint?cursor=XXXX HTTP/1.1

    EXAMPLE RESPONSE:

      status code: 200
      response body:
        {
          nextResults: "https://example.com/apiEndpoint?cursor=YYYY",
          hasNext: true,
          nextCursor: "YYYY",

          previousResults: "https://example.com/apiEndpoint?cursor=ZZZZ",
          hasPrevious: false,
          previousCursor: "ZZZZ",

          results: [...] // Serialized data passed to get_paginated_response()
        }

    EXAMPLE RESPONSE (EMPTY):

      status code: 200
      response body:
        {
          nextResults: null,
          hasNext: false,
          nextCursor: null,

          previousResults: null
          hasPrevious: false,
          previousCursor: null,

          results: []
        }

    CLIENT USE CASE #1: Retrieve all pages and halt

    url = 'https://example.com/apiEndpoint'
    elements = []

    while True:
        json = requests.get(url).json()
        elements.extend(json['results'])
        url = json['nextResults']

        if not json['hasNext']:
            break

    CLIENT USE CASE #2: Continuously retrieve new pages like a feed

    url = 'https://example.com/apiEndpoint'
    queue = Queue()

    while True:
        json = requests.get(url).json()
        results = json['results']

        if len(results) > 0:
            [queue.put(e) for e in results]
            url = json['nextResults']
        else:
            sleep(60) # Or some other retry behavior
    """
    cursor_query_param = 'cursor'

    page_size = 50

    # Model field to use for ordering.  Must be unique, not null, and monotonically increasing.
    #
    # TODO: Add support for non-unique keys.  This should be possible by adding support for ordering by multiple fields.
    # For example, ordering = ('non_unique_field', 'pk') would fully disambiguate records. Would require  compound index
    # on those fields for efficient queries.
    ordering = 'pk'

    pagination_secret_key = getattr(settings, 'PAGINATION_SECRET_KEY', None)

    if pagination_secret_key is not None:
        crypto = Fernet(pagination_secret_key)
        encrypt = True
    else:
        crypto = None
        encrypt = False

    def _get_cursor_limits(self, cursor):
        """
        Parse decrypted cursor and return (lower_limit, upper_limit).
        """
        if cursor is None:
            return None, None

        if cursor.startswith(':'):
            return None, cursor[1:]

        if cursor.endswith(':'):
            return cursor[:-1], None

        raise ValueError('Malformed cursor')

    def _get_elem_key(self, elem):
        """
        Get ordering key for given element.
        """
        return str(getattr(elem, self.ordering))

    def _get_page_cursors(self, page):
        """
        Return (prev_cursor, next_cursor) for given page.
        """
        if len(page) > 0:
            prev_cursor = ':{}'.format(self._get_elem_key(page[0]))
            next_cursor = '{}:'.format(self._get_elem_key(page[-1]))
            return prev_cursor, next_cursor
        else:
            return None, None

    def _decrypt_cursor(self, encrypted):
        if encrypted is not None:
            return self.crypto.decrypt(bytes(encrypted))
        else:
            return encrypted

    def _encrypt_cursor(self, decrypted):
        if decrypted is not None:
            return self.crypto.encrypt(decrypted)
        else:
            return decrypted

    def _build_url(self, request, cursor):
        if cursor is None:
            return None
        else:
            url = request.build_absolute_uri()
            return replace_query_param(url, self.cursor_query_param, cursor)

    def _partition_padded_page(self, padded_page):
        """
        Partition padded page into (page, next_element). padded_page must be reversed if partitioning a page with an
        upper limit.
        """
        assert len(padded_page) <= self.page_size + 1

        iterator = iter(padded_page)
        page = more_itertools.take(self.page_size, iterator)

        extra_elem = None
        try:
            extra_elem = iterator.next()
        except StopIteration:
            pass

        return page, extra_elem

    def paginate_queryset(self, queryset, request, view=None):
        """
        Given a queryset and request, return a page as a list.
        """
        cursor = request.query_params.get(self.cursor_query_param, None)

        if self.encrypt:
            cursor = self._decrypt_cursor(cursor)

        lower_limit, upper_limit = self._get_cursor_limits(cursor)

        assert not (lower_limit and upper_limit), "Invalid state"

        if lower_limit is not None:
            with transaction.atomic():
                # Select up page_size + 1 elements in forward order to populate page and hasNext
                padded_page = queryset.filter(**{self.ordering + '__gt': lower_limit}) \
                                      .order_by(self.ordering)[:self.page_size + 1]
                # Select element for hasPrevious
                prev_elem = queryset.filter(**{self.ordering + '__lte': lower_limit}) \
                                    .order_by('-' + self.ordering) \
                                    .first()

            page, next_elem = self._partition_padded_page(padded_page)
        elif upper_limit is not None:
            with transaction.atomic():
                # Select up page_size + 1 elements in reverse order to populate page and hasPrevious
                padded_page = queryset.filter(**{self.ordering + '__lt': upper_limit}) \
                                      .order_by('-' + self.ordering)[:self.page_size + 1]
                # Select element for hasNext
                next_elem = queryset.filter(**{self.ordering + '__gte': upper_limit}) \
                                    .order_by(self.ordering) \
                                    .first()

            page, prev_elem = self._partition_padded_page(padded_page)
            page = list(reversed(page))
        else:
            # Select up page_size + 1 elements in forward order to populate page and hasNext
            padded_page = queryset.order_by(self.ordering)[:self.page_size + 1]
            prev_elem = None  # Special case--hasPrevious is always False

            page, next_elem = self._partition_padded_page(padded_page)

        prev_cursor, next_cursor = self._get_page_cursors(page)

        if self.encrypt:
            prev_cursor = self._encrypt_cursor(prev_cursor)
            next_cursor = self._encrypt_cursor(next_cursor)

        self.prev_link = self._build_url(request, prev_cursor)
        self.next_link = self._build_url(request, next_cursor)

        self.has_prev = prev_cursor is not None and prev_elem is not None
        self.has_next = next_cursor is not None and next_elem is not None

        self.prev_cursor = prev_cursor
        self.next_cursor = next_cursor

        return page

    def get_paginated_response(self, data):
        """
        Given serialized page of data, return a paginated Response object.
        """
        return Response(OrderedDict([
            ('nextResults', self.next_link),
            ('hasNext', self.has_next),
            ('nextCursor', self.next_cursor),
            ('previousResults', self.prev_link),
            ('hasPrevious', self.has_prev),
            ('previousCursor', self.prev_cursor),
            ('results', data)]))
