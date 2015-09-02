import inspect
import re
import sys
from UserDict import UserDict

from rest_framework.serializers import ValidationError

from .utils import domain
import serializers


class AnnotatedDict(UserDict, object):

    def __init__(self, dictionary):
        super(AnnotatedDict, self).__init__(dictionary)

        self.versions = []
        self.version_errors = {}
        self.version = None


class ComponentsSerializer(object):

    def __init__(self, badge_instance, badge_class, issuer):

        # These properties are now dict-like adding metadata within properties
        self.badge_instance = \
            AnnotatedDict(badge_instance.copy())
        self.badge = AnnotatedDict(badge_class.copy())
        self.issuer = AnnotatedDict(issuer.copy())

        self.json = badge_instance.copy()
        self.json['badge'] = badge_class.copy()
        self.json['badge']['issuer'] = issuer.copy()

        self.components = (
            ('issuer', self.issuer),
            ('badge_class', self.badge),
            ('badge_instance', self.badge_instance),
        )

        self.version_signature = re.compile(r"[Vv][0-9](_[0-9])+$")

        # Serializers check, field presence and type conformance
        for module_name, component in self.components:
            self._add_versions(component, module_name)
            self._evaluate_version(component)

    def _add_versions(self, component, module_name):
        module = getattr(serializers, module_name)
        classes = zip(*inspect.getmembers(sys.modules[module.__name__],
                                          inspect.isclass))[0]

        component.versions = filter(
            lambda class_: self.version_signature.search(class_), classes)

    def _evaluate_version(self, component):
        component.version = None
        for version in component.versions:

            SerializerClass = getattr(serializers, version)
            serializer = SerializerClass(
                data=component.data,
            )

            if not serializer.is_valid():
                component.version_errors[version] = serializer.errors
            else:
                component.version = self.get_version(version)
                component.serializer = SerializerClass
                #  component.serializer_instance = serializer

    def get_version(self, version):
        try:
            return self.version_signature.search(version).group() \
                .replace('_', '.').replace('V', 'v')
        except AttributeError:
            return None

    def is_valid(self):
        return (self.badge_instance.version and self.badge.version and
                self.issuer.version)

    def validate(self, raise_exception=True):
        """
        Validation that requires access to multiple components.
        """
        same_version_components = (self.badge.version == self.issuer.version ==
                                   self.badge_instance.version)
        if not same_version_components:
            raise ValidationError(
                "Components assembled with different specification versions.")

        if self.badge_instance.version.startswith('v1'):
            resources = filter(None, [self.badge_instance['verify']['url'],
                                      self.badge_instance['badge'],
                                      self.badge_instance.get('url'),
                                      self.badge_instance.get('id')])
            same_domains = len(set([domain(resource)
                                    for resource in resources])) == 1
            if not same_domains:
                raise ValidationError(
                    "Component resource references don't share the same \
                    domain.")

        return True

    # def save(self):
    #     issuer = self.issuer.serializer_instance.save()
    #     badge_class = self.badge.serializer_instance.save(issuer=issuer)
    #     badge_instance = self.badge_instance.serializer_instance.save(
    #         badge_class=badge_class)
    #     return badge_instance
