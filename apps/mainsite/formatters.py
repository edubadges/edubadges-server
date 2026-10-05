import datetime

from pythonjsonlogger import jsonlogger


class JsonFormatter(jsonlogger.JsonFormatter):
    default_time_format = "%Y-%m-%dT%H:%M:%S.%f%z"

    def converter(self, timestamp):
        return datetime.datetime.fromtimestamp(timestamp, tz=datetime.UTC)

    def formatTime(self, record, datefmt=None):  # noqa: N802
        dt = self.converter(record.created)
        return dt.strftime(datefmt or self.default_time_format)
