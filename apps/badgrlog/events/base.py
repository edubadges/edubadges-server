import datetime

class BaseBadgrEvent(object):

    def get_type(self):
        return self.__class__.__name__

    def get_context(self):
        return "https://badgr.io/json-ld/v1"

    def to_representation(self):
        raise NotImplementedError("subclasses must provide a to_representation method")

    def compacted(self):
        data = self.to_representation()
        data.update({
            '@context': self.get_context(),
            'type': 'Action',
            'actionType': self.get_type(),
            'timestamp': datetime.datetime.now().isoformat()
        })
        return data
