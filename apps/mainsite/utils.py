"""
Utility functions and constants that might be used across the project.
"""
from __future__ import unicode_literals

import StringIO
import base64
import hashlib
import re
import urlparse
import uuid

import os
import requests
from django.apps import apps
from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import DefaultStorage
from django.core.urlresolvers import get_callable, reverse
from xml.etree import cElementTree as ET


class ObjectView(object):
    """
    A simple utility that allows Rest Framework Serializers to serialize dict-based input
    when there is no appropriate model Class to instantiate.

    Instantiate an ObjectView(source_dict) in the serializer's to_internal_value() method.
    """
    def __init__(self, d):
        self.__dict__ = d

    def __unicode__(self):
        return str(self.__dict__)


slugify_function_path = \
    getattr(settings, 'AUTOSLUG_SLUGIFY_FUNCTION', 'autoslug.utils.slugify')

slugify = get_callable(slugify_function_path)

def installed_apps_list():
    installed_apps = []
    for app in ('issuer', 'composition', 'badgebook'):
        if apps.is_installed(app):
            installed_apps.append(app)
    return installed_apps


def client_ip_from_request(request):
    """Returns the IP of the request, accounting for the possibility of being behind a proxy.
    """
    ip = request.META.get("HTTP_X_FORWARDED_FOR", None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(", ")[0]
    else:
        ip = request.META.get("REMOTE_ADDR", "")
    return ip


class OriginSettingsObject(object):
    DefaultOrigin = "http://localhost:8000"

    @property
    def DEFAULT_HTTP_PROTOCOL(self):
        parsed = urlparse.urlparse(self.HTTP)
        return parsed.scheme

    @property
    def HTTP(self):
        return getattr(settings, 'HTTP_ORIGIN', OriginSettingsObject.DefaultOrigin)

OriginSetting = OriginSettingsObject()

"""
Cache Utilities
"""
def filter_cache_key(key, key_prefix, version):
    generated_key = ':'.join([key_prefix, str(version), key])
    if len(generated_key) > 250:
        return hashlib.md5(generated_key).hexdigest()
    return generated_key


def verify_svg(fileobj):
    """
    Check if provided file is svg
    from: https://gist.github.com/ambivalentno/9bc42b9a417677d96a21
    """
    fileobj.seek(0)
    tag = None
    try:
        for event, el in ET.iterparse(fileobj, events=(b'start',)):
            tag = el.tag
            break
    except ET.ParseError:
        pass
    return tag == '{http://www.w3.org/2000/svg}svg'


def fetch_remote_file_to_storage(remote_url, upload_to=''):
    """
    Fetches a remote url, and stores it in DefaultStorage
    :return: (status_code, new_storage_name)
    """
    store = DefaultStorage()
    r = requests.get(remote_url, stream=True)
    if r.status_code == 200:
        name, ext = os.path.splitext(urlparse.urlparse(r.url).path)
        storage_name = '{upload_to}/cached/{filename}{ext}'.format(
            upload_to=upload_to,
            filename=hashlib.md5(remote_url).hexdigest(),
            ext=ext)
        if not store.exists(storage_name):
            buf = StringIO.StringIO(r.content)
            store.save(storage_name, buf)
        return r.status_code, storage_name
    return r.status_code, None


def generate_entity_uri():
    """
    Generate a unique url-safe identifier
    """
    entity_uuid = uuid.uuid4()
    b64_string = base64.urlsafe_b64encode(entity_uuid.bytes)
    b64_trimmed = re.sub(r'=+$', '', b64_string)
    return b64_trimmed


def first_node_match(graph, condition):
    """return the first dict in a list of dicts that matches condition dict"""
    for node in graph:
        if all(item in node.items() for item in condition.items()):
            return node


def get_tool_consumer_instance_guid():
    guid = getattr(settings, 'EXTERNALTOOL_CONSUMER_INSTANCE_GUID', None)
    if guid is None:
        guid = cache.get("external_tool_consumer_instance_guid")
        if guid is None:
            guid = "badgr-tool-consumer:{}".format(generate_entity_uri())
            cache.set("external_tool_consumer_instance_guid", guid, timeout=None)
    return guid


def list_of(value):
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    return [value]


class EmailMessageMaker:

    @staticmethod
    def create_student_badge_request_email(badge_class):
        mail_template = 'Dear student, \n\n ' \
                        '\tYou have successfully requested the following badge. \n\n' \
                        '\t{}, {} \n\n' \
                        '\tPlease wait for the issuer of this badge to accept your request. \n\n' \
                        'Regards, \n\n' \
                        'The Edubadges team'
        return mail_template.format(badge_class.name, badge_class.public_url)

    @staticmethod
    def create_issuer_staff_badge_request_email(badge_classes):
        badge_classes_string = ''.join(
            ['\t- {name} (issuer: {issuer})\n\n'.format(issuer=badge_class.issuer.name, name=badge_class.name) for
             badge_class in badge_classes])
        mail_template = 'Dear staff member, \n\n ' \
                        '\tYou have new badge requests for the following badge class{0}. \n\n' \
                        '{1}' \
                        '\tThese new requests have been made in the last 24 hours. \n\n' \
                        'Regards, \n\n' \
                        'The Edubadges team'
        plural = 'es' if len(badge_classes) > 1 else ''
        return mail_template.format(plural, badge_classes_string)

    @staticmethod
    def create_staff_member_addition_email(url, issuer, role):
        mail_template = 'Dear Sir/Madam, \n\n' \
                        'You have been asked to join the issuer {issuer_name} as staff member\n\n' \
                        'with the role: {role}. If you accept please click on the link below. \n\n' \
                        '{url} \n\n' \
                        'If you do not want to accept, then ignore this email.' \
                        '\n\n' \
                        'Kind regards, \n\n' \
                        'The Edubadges team'
        return mail_template.format(**{'issuer_name': issuer.name,
                                       'role': role,
                                       'url': url})
