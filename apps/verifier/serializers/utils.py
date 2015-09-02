class ObjectView(object):
    # TODO: What is this?
    def __init__(self, d):
        self.__dict__ = d

    def __unicode__(self):
        return str(self.__dict__)
