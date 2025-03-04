import logging

from .events.base import BaseBadgrEvent


class BadgrLogger(object):
    def __init__(self, name='Badgr.Events'):
        self.logger = logging.getLogger(name)

    def event(self, event):
        if not isinstance(event, BaseBadgrEvent):
            raise NotImplementedError()
        obj = event.compacted()
        self.logger.info(obj)


