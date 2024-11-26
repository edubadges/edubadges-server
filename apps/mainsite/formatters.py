# Created by wiggins@concentricsky.com on 8/27/15.

import datetime

from django.utils import timezone
from pythonjsonlogger import jsonlogger


class JsonFormatter(jsonlogger.JsonFormatter):
    default_time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    def converter(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)

    def formatTime(self, record, datefmt=None):
        dt = self.converter(record.created)
        return dt.strftime(datefmt if datefmt else self.default_time_format)

