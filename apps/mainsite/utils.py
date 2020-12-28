"""
Utility functions and constants that might be used across the project.
"""

import base64
import hashlib
import io
import os
import re
import tempfile
import urllib.parse
import uuid
import webbrowser
from io import BytesIO
from PIL import Image
from premailer import transform
from xml.etree import cElementTree as ET

import requests
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.files.storage import DefaultStorage
from django.core import mail
from django.template.loader import render_to_string
from django.urls import get_callable, reverse
from django.utils.html import format_html

slugify_function_path = \
    getattr(settings, 'AUTOSLUG_SLUGIFY_FUNCTION', 'autoslug.utils.slugify')

slugify = get_callable(slugify_function_path)


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
        parsed = urllib.parse.urlparse(self.HTTP)
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
        name, ext = os.path.splitext(urllib.parse.urlparse(r.url).path)
        storage_name = '{upload_to}/cached/{filename}{ext}'.format(
            upload_to=upload_to,
            filename=hashlib.md5(remote_url.encode()).hexdigest(),
            ext=ext)
        if not store.exists(storage_name):
            buf = io.BytesIO(r.content)
            store.save(storage_name, buf)
        return r.status_code, storage_name
    return r.status_code, None


def generate_entity_uri():
    """
    Generate a unique url-safe identifier
    """
    entity_uuid = uuid.uuid4()
    b64_string = base64.urlsafe_b64encode(entity_uuid.bytes)
    b64_trimmed = re.sub(b'=+$', b'', b64_string)
    return b64_trimmed.decode()


def first_node_match(graph, condition):
    """return the first dict in a list of dicts that matches condition dict"""
    for node in graph:
        if all(item in list(node.items()) for item in list(condition.items())):
            return node

def list_of(value):
    if value is None:
        return []
    elif isinstance(value, list):
        return value
    return [value]


def open_mail_in_browser(html):
    tmp = tempfile.NamedTemporaryFile(delete=False)
    path = tmp.name + ".html"
    f = open(path, "w")
    f.write(html)
    f.close()
    webbrowser.open("file://" + path)


class EmailMessageMaker:

    @staticmethod
    def create_enrollment_denied_email(enrollment):
        template = 'email/enrollment_denied.html'
        email_vars = {'public_badge_url': enrollment.badge_class.public_url,
                      'badgeclass_name': enrollment.badge_class.name,
                      'recipient_name': enrollment.user.full_name}
        return render_to_string(template, email_vars)

    @staticmethod
    def create_staff_rights_changed_email(staff_membership):
        template = 'email/staff_rights_changed.html'
        email_vars = {'recipient_name': staff_membership.user.full_name,
                      'entity_type': staff_membership.object.__class__.__name__.lower(),
                      'entity_type_dutch': staff_membership.object.DUTCH_NAME.lower(),
                      'entity_name': staff_membership.object.name}
        return render_to_string(template, email_vars)

    @staticmethod
    def create_user_invited_email(provisionment, login_link):
        template = 'email/staff_invitation.html'
        invitee_name = 'Sir/Madam'
        invitee_name_dutch = 'Heer/Mevrouw'
        if provisionment.user:
            invitee_name = provisionment.user.full_name
            invitee_name_dutch = provisionment.user.full_name
        email_vars = {'login_link': login_link,
                      'invited_by_name': provisionment.created_by.full_name,
                      'invitee_name': invitee_name,
                      'invitee_name_dutch': invitee_name_dutch,
                      'entity_type': provisionment.entity.__class__.__name__.lower(),
                      'entity_type_dutch': provisionment.entity.DUTCH_NAME.lower(),
                      'entity_name': provisionment.entity.name,
                      'support_email_address': 'support@edubadges.nl'}
        return render_to_string(template, email_vars)

    @staticmethod
    def create_student_badge_request_email(user, badge_class):
        template = 'email/requested_badge.html'
        email_vars = {'public_badge_url': badge_class.public_url,
                      'badge_name': badge_class.name,
                      'user_name': user.get_full_name()}
        return render_to_string(template, email_vars)

    @staticmethod
    def create_staff_member_addition_email(new_staff_membership):
        template = 'email/new_role.html'
        entity = new_staff_membership.object
        entity_type = entity.__class__.__name__.lower()
        entity_type_dutch = entity.DUTCH_NAME.lower()
        determiner = 'an' if entity_type[0] in 'aeiou' else 'a'
        email_vars = {'staff_page_url': new_staff_membership.staff_page_url,
                      'entity_type': entity_type,
                      'entity_type_dutch': entity_type_dutch,
                      'entity_name': entity.name,
                      'determiner': determiner}
        return render_to_string(template, email_vars)

    @staticmethod
    def create_earned_badge_mail(assertion):
        badgeclass = assertion.badgeclass
        template = 'email/earned_badge.html'
        background = Image.open(badgeclass.image.path).convert("RGBA")
        overlay = Image.open(finders.find('images/example_overlay.png')).convert("RGBA")
        if overlay.width != background.width:
            width_ratio = background.width/overlay.width
            new_background_height = background.height*width_ratio
            new_background_size = (overlay.width, new_background_height)
            background.thumbnail((new_background_size), Image.ANTIALIAS)
        position = (0, background.height//4)
        background.paste(overlay, position, overlay)
        buffered = BytesIO()
        background.save(buffered, format="PNG")
        encoded_string = base64.b64encode(buffered.getvalue()).decode()
        email_vars = {
            'badgeclass_image': 'data:image/png;base64,{}'.format(encoded_string),
            'issuer_image': badgeclass.issuer.image_url(),
            'issuer_name': badgeclass.issuer.name,
            'faculty_name': badgeclass.issuer.faculty.name,
            'assertion_url': assertion.student_url,
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
        }
        return render_to_string(template, email_vars)


def send_mail(subject, message, recipient_list, html_message=None):
    if settings.LOCAL_DEVELOPMENT_MODE:
        open_mail_in_browser(html_message)
    if html_message:
        html_with_inline_css = transform(html_message)
        msg = mail.EmailMessage(subject=subject, body=html_with_inline_css, from_email=None, to=recipient_list)
        msg.content_subtype = "html"
        msg.send()
    else:
        mail.send_mail(subject, message, from_email=None, recipient_list=recipient_list, html_message=html_message)


def admin_list_linkify(field_name, label_param=None):
    """
    Converts a foreign key value into clickable links for the admin list view.

    field_name is the column name of the foreignkey
    label_param is the param you want to show in the list as label of the referenced object
    """
    def _linkify(obj):
        linked_obj = getattr(obj, field_name)
        if linked_obj is None:
            return '-'
        app_label = linked_obj._meta.app_label
        model_name = linked_obj._meta.model_name
        view_name = f'admin:{app_label}_{model_name}_change'
        link_url = reverse(view_name, args=[linked_obj.pk])
        if label_param:
            linked_obj = getattr(linked_obj, label_param)
        return format_html('<a href="{}">{}</a>', link_url, linked_obj)

    _linkify.short_description = field_name  # Sets column name
    return _linkify