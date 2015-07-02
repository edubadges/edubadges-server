import logging
from os import path

from django.conf import settings


class BadgrFilter(logging.Filter):
    def filter(self, record):
        return record.name == 'badgr'


class SiteLogger(object):

    def __init__(self, logger_name, log_file, prefix=''):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)
        self.logger.addHandler(
            logging.FileHandler(
                path.join(settings.LOGS_DIR, log_file), delay=True
            )
        )
        self.prefix = prefix

    def debug(self, message):
        self.logger.debug(self.prefix + '|' + message)


badgr_log = SiteLogger('ShoppingLogger', 'badgr.log', 'BADGR')
