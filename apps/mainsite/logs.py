import logging


class BadgrFilter(logging.Filter):
    def filter(self, record):
        return record.name == 'badgr'
