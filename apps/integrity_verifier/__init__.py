import inspect
import re
import sys
from urlparse import urlparse
from UserDict import UserDict

import requests

import serializers


class RemoteBadgeInstance(object):
    """
    A RemoteBadgeInstance is a remotely fetched in-memory representation of
    a badge instance, containing its corresponding badge (class) and issuer.
    """

    def __init__(self, instance_url, recipient_id=None):
        self.instance_url = instance_url
        self.recipient_id = recipient_id

        self.badge_instance = requests.get(instance_url).json()
        self.json = self.badge_instance.copy()

        self.badge = requests.get(self.badge_instance['badge']).json()
        self.json['badge'] = self.badge

        self.issuer = requests.get(self.badge['issuer']).json()
        self.json['badge']['issuer'] = self.issuer

    def __getitem__(self, key):
        return self.badge_instance[key]

    def __repr__(self):
        return str(self.badge_instance)


class AnnotatedDict(UserDict, object):

    def __init__(self, dictionary):
        super(AnnotatedDict, self).__init__(dictionary)

        self.versions = []
        self.version_errors = {}
        self.version = None


class AnalyzedBadgeInstance(RemoteBadgeInstance):

    def __init__(self, badge_instance, recipient_id=None):
        if not isinstance(badge_instance, RemoteBadgeInstance):
            raise TypeError('Expected RemoteBadgeInstance')

        self.instance_url = badge_instance.instance_url
        self.recipient_id = (recipient_id
                             or getattr(badge_instance, 'recipient_id', None))
        self.json = badge_instance.json.copy()

        # These properties are now dict-like adding metadata within properties
        self.badge_instance = \
            AnnotatedDict(badge_instance.badge_instance.copy())
        self.badge = AnnotatedDict(badge_instance.badge.copy())
        self.issuer = AnnotatedDict(badge_instance.issuer.copy())

        self.non_component_errors = []
        self.check_origin()

        self.version_signature = re.compile(r"[Vv][0-9](_[0-9])+$")

        components = (
            ('badge_instance', self.badge_instance),
            ('badge_class', self.badge),
            ('issuer', self.issuer))

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

        component.version = None
        for version in component.versions:
            SerializerClass = getattr(serializers, version)
            serializer = SerializerClass(
                data=component.data,
                context={'recipient_id': self.recipient_id})

            if not serializer.is_valid():
                component.version_errors[version] = serializer.errors
            else:
                component.version = self.get_version(version)

    def get_version(self, version):
        try:
            return self.version_signature.search(version).group() \
                .replace('_', '.').replace('V', 'v')
        except AttributeError:
            return None

    def check_origin(self):
        same_domain = (urlparse(self.instance_url).netloc
                       == urlparse(self.badge_instance['badge']).netloc
                       == urlparse(self.badge['issuer']['url']).netloc)
        if not same_domain:
            self.non_component_errors.append(
                ('domain', "Badge components don't share the same domain."))

    def __getattr__(self, key):
        base_properties = ['instance_url', 'recipient_id',
                           'badge', 'issuer', 'json']
        if key not in base_properties:
            return getattr(self.badge_instance, key)

    def __getitem__(self, key):
        return self.badge_instance[key]

    def __repr__(self):
        return str(self.badge_instance)
