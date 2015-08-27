# Created by wiggins@concentricsky.com on 8/27/15.


class BaseBadgrEvent(object):
    def __init__(self):
        pass

    def get_type(self):
        return self.__class__.__name__

    def get_context(self):
        return "http://badgr.io/json-ld/"

    def to_representation(self):
        raise NotImplementedError("subclasses must provide a to_representation method")

    def compacted(self):
        data = self.to_representation()
        data.update({
            '@context': self.get_context(),
            '@type': self.get_type(),
        })
        return data
