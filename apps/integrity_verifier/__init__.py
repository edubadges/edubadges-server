import inspect
import re
import sys
from UserDict import UserDict

import requests

import serializers


class AnalyzedBadgeInstance(object):

    def __init__(self, badge_instance, recipient_id=None):
        if not isinstance(badge_instance, RemoteBadgeInstance):
            raise TypeError('Expected RemoteBadgeInstance')

        self.recipient_id = (recipient_id
                             or getattr(badge_instance, 'recipient_id', None))

        self.version_signature = re.compile(r"[Vv][0-9](_[0-9])+$")

        components = (
            ('badge_instance', badge_instance),
            ('badge_class', badge_instance.badge),
            ('issuer', badge_instance.issuer))

        for module_name, component in components:
            self.add_versions(component, module_name)
            self.evaluate_version(component)

    def add_versions(self, component, module_name):
        module = getattr(serializers, module_name)
        classes = zip(*inspect.getmembers(sys.modules[module.__name__],
                                          inspect.isclass))[0]

        component.versions = filter(
            lambda class_: self.version_signature.search(class_), classes)

    def evaluate_version(self, component):

        for version in component.versions:
            SerializerClass = getattr(serializers, version)
            serializer = SerializerClass(
                data=component, context={'recipient_id': self.recipient_id})

            if not serializer.is_valid():
                component.version_errors = serializer.errors

            component.version = self.get_version(version)

    def get_version(self, version):
        try:
            return self.version_signature.search(version).group() \
                .replace('_', '.').replace('V', 'v')
        except AttributeError:
            return None


class AnnotatableDict(UserDict, object):
    """
    A subclass of AnnotatableDict inherits a self.errors list
    """

    def __init__(self, a_dict):
        super(AnnotatableDict, self).__init__(a_dict)
        self.errors = []


class RemoteBadgeInstance(AnnotatableDict):
    """
    A RemoteBadgeInstance is a remotely fetched in-memory representation of
    a badge instance, containing its corresponding badge (class) and issuer.
    """

    def __init__(self, instance_url, recipient_id=None):
        self.non_component_errors = []
        self.instance_url = instance_url
        self.recipient_id = recipient_id

        self.badge_instance = requests.get(instance_url).json()
        self.json = self.badge_instance.copy()

        self.badge = AnnotatableDict(
            requests.get(self.badge_instance['badge']).json())
        self.json['badge'] = self.badge

        self.issuer = AnnotatableDict(
            requests.get(self.badge['issuer']).json())
        self.json['badge']['issuer'] = self.issuer

        super(RemoteBadgeInstance, self).__init__(self.badge_instance)

    def __getitem__(self, key):
        return self.badge_instance[key]

    def __repr__(self):
        return str(self.badge_instance)


#  from urlparse import urlparse
#  same_domain = (urlparse(badge_instance.instance_url).netloc
#                 == urlparse(badge_instance['badge']).netloc
#                 == urlparse(badge_instance.badge['issuer']).netloc)
#  if not same_domain:
#      self.non_component_errors.append(
#          ('domain', "Badge components don't share the same domain."))
