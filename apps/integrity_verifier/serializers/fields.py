from datetime import datetime
import re

from django.utils.dateparse import parse_datetime

from rest_framework import serializers


class BadgeDateTimeField(serializers.Field):

    default_error_messages = {
        'not_int_or_str': 'Invalid format. Expected an int or str.',
        'bad_str': 'Invalid format. String is not ISO 8601 or unix timestamp.',
        'bad_int': 'Invalid format. Unix timestamp is out of range.',
    }

    def to_internal_value(self, value):
        if isinstance(value, (str, unicode)):
            try:
                return datetime.utcfromtimestamp(float(value))
            except ValueError:
                pass

            value = parse_datetime(value)
            if not value:
                self.fail('bad_str')
            return value
        elif isinstance(value, int) or isinstance(value, float):
            try:
                return datetime.utcfromtimestamp(value)
            except ValueError:
                self.fail('bad_int')
        else:
            self.fail('not_int_or_str')


class HashString(serializers.Field):
    """
    A representation of a badge recipient identifier that indicates a hashing
    algorithm and hashed value.
    """

    def to_internal_value(self, data):
        try:
            data = data.lower()
        except AttributeError:
            raise serializers.ValidationError("Invalid data. Expected a str.")

        patterns = (
            r'^sha1\$[a-f0-9]{40}$',
            r'^sha256\$[a-f0-9]{64}$',
            r'^md5\$[a-fA-F0-9]{32}$'
        )

        if not any(re.match(pattern, data) for pattern in patterns):
            raise serializers.ValidationError(
                "Invalid data. String is not recognizably formatted.")

        return data
