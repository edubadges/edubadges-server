import logging
import os

from django.conf import settings


class BadgrFilter(logging.Filter):
    def filter(self, record):
        return True
        return record.name == 'badgr'


class SiteLogger(object):

    def __init__(self, logger_name, log_file, prefix=''):
        self.logger = logging.getLogger(logger_name)
        self.logger.setLevel(logging.DEBUG)

        full_filename = os.path.join(settings.LOGS_DIR, log_file)
        if not os.path.exists(full_filename):
            with open(full_filename, 'w+'):
                pass
        self.logger.addHandler(
            logging.FileHandler(full_filename)
        )
        self.prefix = prefix

    def debug(self, message):
        self.logger.debug(self.prefix + '|' + message)

badgr_log = SiteLogger('badgr', 'badgr.log', 'BADGR')
