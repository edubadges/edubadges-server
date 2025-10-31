"""
Utility functions and constants that might be used across the project.
"""

import base64
import datetime
import hashlib
import io
import locale
import math
import os
import pathlib
import re
import tempfile
import urllib.parse
import uuid
import webbrowser
from io import BytesIO
from xml.etree import cElementTree as ET

import cairosvg
import requests
from django.conf import settings
from django.contrib.staticfiles import finders
from django.core import mail
from django.core.exceptions import ValidationError
from django.core.files.storage import DefaultStorage, default_storage
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.template.loader import render_to_string
from django.urls import get_callable, reverse
from django.utils.html import format_html
from PIL import Image, ImageDraw, ImageEnhance, ImageFont
from premailer import transform
from resizeimage.resizeimage import resize_contain

from institution.testfiles.helper import institution_image

slugify_function_path = getattr(settings, 'AUTOSLUG_SLUGIFY_FUNCTION', 'autoslug.utils.slugify')

slugify = get_callable(slugify_function_path)


def client_ip_from_request(request):
    """Returns the IP of the request, accounting for the possibility of being behind a proxy."""
    ip = request.headers.get('x-forwarded-for', None)
    if ip:
        # X_FORWARDED_FOR returns client1, proxy1, proxy2,...
        ip = ip.split(', ')[0]
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


class OriginSettingsObject(object):
    DefaultOrigin = 'http://localhost:8000'

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
        encoded_string = generated_key.encode('utf-8')
        return hashlib.md5(encoded_string).hexdigest()
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
            upload_to=upload_to, filename=hashlib.md5(remote_url.encode(), usedforsecurity=False).hexdigest(), ext=ext
        )
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
    path = tmp.name + '.html'
    f = open(path, 'w')
    f.write(html)
    f.close()
    webbrowser.open('file://' + path)


class EmailMessageMaker:
    @staticmethod
    def _create_example_image(badgeclass):
        path = badgeclass.image.path
        if path.endswith('.svg'):
            with open(path, 'rb') as input_svg:
                svg = input_svg.read()
                encoded = base64.b64encode(svg).decode()
                return 'data:image/svg+xml;base64,{}'.format(encoded)
        else:
            background = Image.open(badgeclass.image.path).convert('RGBA')

        overlay = Image.open(finders.find('images/example_overlay.png')).convert('RGBA')
        if overlay.width != background.width:
            width_ratio = background.width / overlay.width
            new_background_height = background.height * width_ratio
            new_background_size = (overlay.width, new_background_height)
            background.thumbnail((new_background_size), Image.LANCZOS)
        position = (0, background.height // 4)
        background.paste(overlay, position, overlay)
        buffered = BytesIO()
        background.save(buffered, format='PNG')
        encoded_string = base64.b64encode(buffered.getvalue()).decode()
        return 'data:image/png;base64,{}'.format(encoded_string)

    @staticmethod
    def create_enrollment_denied_email(enrollment):
        template = 'email/enrollment_denied.html'
        email_vars = {
            'public_badge_url': enrollment.badge_class.public_url,
            'badgeclass_name': enrollment.badge_class.name,
            'recipient_name': enrollment.user.full_name,
            'deny_reason': enrollment.deny_reason,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_assertion_revoked_email(badge_instance):
        template = 'email/assertion_revoked.html'
        email_vars = {
            'public_badge_url': badge_instance.badgeclass.public_url,
            'badgeclass_name': badge_instance.badgeclass.name,
            'recipient_name': badge_instance.user.full_name,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, 'archived'),
            'revocation_reason': badge_instance.revocation_reason,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_direct_award_deleted_email(direct_award):
        template = 'email/awarded_badge_deleted.html'
        email_vars = {
            'public_badge_url': direct_award.badgeclass.public_url,
            'badgeclass_name': direct_award.badgeclass.name,
            'recipient_name': direct_award.recipient_email,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, 'archived'),
            'revocation_reason': direct_award.revocation_reason,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_staff_rights_changed_email(staff_membership):
        template = 'email/staff_rights_changed.html'
        email_vars = {
            'recipient_name': staff_membership.user.full_name,
            'entity_type': staff_membership.object.__class__.__name__.lower(),
            'entity_type_dutch': staff_membership.object.DUTCH_NAME.lower(),
            'entity_name': staff_membership.object.name,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_user_invited_email(provisionment, login_link):
        template = 'email/staff_invitation.html'
        invitee_name = 'Sir/Madam'
        invitee_name_dutch = 'Heer/Mevrouw'
        if provisionment.user:
            invitee_name = provisionment.user.full_name
            invitee_name_dutch = provisionment.user.full_name
        email_vars = {
            'login_link': login_link,
            'invited_by_name': provisionment.created_by.full_name,
            'invitee_name': invitee_name,
            'invitee_name_dutch': invitee_name_dutch,
            'entity_type': provisionment.entity.__class__.__name__.lower(),
            'entity_type_dutch': provisionment.entity.DUTCH_NAME.lower(),
            'entity_name': provisionment.entity.name,
            'support_email_address': 'support@edubadges.nl',
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_student_badge_request_email(user, badge_class):
        template = 'email/requested_badge.html'
        email_vars = {
            'public_badge_url': badge_class.public_url,
            'badge_name': badge_class.name,
            'user_name': user.get_full_name(),
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_endorsement_requested_mail(current_user, user, endorsement):
        template = 'email/notification_endorsement.html'
        email_vars = {
            'endorsement': endorsement,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, f'badgeclass/{endorsement.endorser.entity_id}/endorsed'),
            'ui_url_notifications': urllib.parse.urljoin(settings.UI_URL, 'notifications'),
            'user': user,
            'current_user': current_user,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def reject_approve_endorsement_mail(user, endorsement, accepted):
        template = 'email/accepted_rejected_endorsement.html'
        email_vars = {
            'endorsement': endorsement,
            'action_en': 'accepted' if accepted else 'rejected',
            'action_nl': 'geaccepteerd' if accepted else 'afgewezen',
            'ui_url': urllib.parse.urljoin(
                settings.UI_URL, f'badgeclass/{endorsement.endorsee.entity_id}/endorsements'
            ),
            'user': user,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_staff_member_addition_email(new_staff_membership):
        template = 'email/new_role.html'
        entity = new_staff_membership.object
        entity_type = entity.__class__.__name__.lower()
        entity_type_dutch = entity.DUTCH_NAME.lower()
        determiner = 'an' if entity_type[0] in 'aeiou' else 'a'
        email_vars = {
            'staff_page_url': new_staff_membership.staff_page_url,
            'entity_type': entity_type,
            'entity_type_dutch': entity_type_dutch,
            'entity_name': entity.name,
            'determiner': determiner,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_direct_award_student_mail(direct_award):
        badgeclass = direct_award.badgeclass
        template = 'email/earned_direct_award_new.html'
        badgeclass_image = EmailMessageMaker._create_example_image(badgeclass)
        en_end_date = direct_award.expiration_date.strftime('%d %B %Y')
        locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
        nl_end_date = direct_award.expiration_date.strftime('%d %B %Y')
        locale.setlocale(locale.LC_ALL, os.environ.get('LC_ALL', 'en_US.UTF-8'))
        faculty = badgeclass.issuer.faculty
        institution_name = faculty.name if faculty.on_behalf_of else faculty.institution.name
        email_vars = {
            'badgeclass_image': badgeclass_image,
            'issuer_image': badgeclass.issuer.image_url(),
            'issuer_name': badgeclass.issuer.name,
            'faculty_name': faculty.name,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, 'direct-awards'),
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
            'institution_name': institution_name,
            'en_da_enddate': en_end_date,
            'nl_da_enddate': nl_end_date,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_enrolment_notification_mail(badge_class, student, created_enrollment):
        template = 'email/notification_badge.html'
        email_vars = {
            'user_email': student.email,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, f'badgeclass/{badge_class.entity_id}/enrollments'),
            'ui_url_notifications': urllib.parse.urljoin(settings.UI_URL, 'notifications'),
            'badgeclass_name': badge_class.name,
            'enrollment_evidence_description': created_enrollment.narrative,
            'enrollment_evidence_url': created_enrollment.evidence_url,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def direct_award_reminder_student_mail(direct_award):
        badgeclass = direct_award.badgeclass
        template = 'email/reminder_direct_award_new.html'
        badgeclass_image = EmailMessageMaker._create_example_image(badgeclass)

        en_create_date = direct_award.created_at.strftime('%d %B %Y')
        en_end_date = direct_award.expiration_date.strftime('%d %B %Y')
        locale.setlocale(locale.LC_ALL, 'nl_NL.UTF-8')
        nl_create_date = direct_award.created_at.strftime('%d %B %Y')
        nl_end_date = direct_award.expiration_date.strftime('%d %B %Y')
        locale.setlocale(locale.LC_ALL, os.environ.get('LC_ALL', 'en_US.UTF-8'))
        faculty = badgeclass.issuer.faculty
        institution_name = faculty.name if faculty.on_behalf_of else faculty.institution.name
        email_vars = {
            'badgeclass_image': badgeclass_image,
            'issuer_image': badgeclass.issuer.image_url(),
            'issuer_name': badgeclass.issuer.name,
            'faculty_name': faculty.name,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, 'direct-awards'),
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
            'institution_name': institution_name,
            'da_enddate_nl': nl_end_date,
            'da_enddate_en': en_end_date,
            'da_creationdate_nl': nl_create_date,
            'da_creationdate_en': en_create_date,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def direct_award_expired_student_mail(direct_award):
        badgeclass = direct_award.badgeclass
        template = 'email/expired_direct_award_new.html'
        badgeclass_image = EmailMessageMaker._create_example_image(badgeclass)
        email_vars = {
            'badgeclass_image': badgeclass_image,
            'issuer_image': badgeclass.issuer.image_url(),
            'issuer_name': badgeclass.issuer.name,
            'faculty_name': badgeclass.issuer.faculty.name,
            'ui_url': urllib.parse.urljoin(settings.UI_URL, 'direct-awards'),
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
            'institution_name': badgeclass.issuer.faculty.institution.name,
            'da_enddate': direct_award.expiration_date,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_earned_badge_mail(assertion):
        badgeclass = assertion.badgeclass
        template = 'email/earned_badge.html'
        badgeclass_image = EmailMessageMaker._create_example_image(badgeclass)
        email_vars = {
            'badgeclass_image': badgeclass_image,
            'issuer_image': badgeclass.issuer.image_url(),
            'issuer_name': badgeclass.issuer.name,
            'faculty_name': badgeclass.issuer.faculty.name,
            'assertion_url': assertion.student_url,
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_direct_award_bundle_mail(direct_award_bundle):
        badgeclass = direct_award_bundle.badgeclass
        template = 'email/teacher_direct_award_bundle_notification.html'
        email_vars = {
            'direct_award_count': direct_award_bundle.direct_award_count,
            'direct_award_bundle_url': direct_award_bundle.url,
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_scheduled_direct_award_bundle_mail(direct_award_bundle):
        badgeclass = direct_award_bundle.badgeclass
        template = 'email/teacher_direct_award_bundle_scheduled_notification.html'
        email_vars = {
            'direct_award_count': direct_award_bundle.direct_award_scheduled_count,
            'direct_award_bundle_url': direct_award_bundle.url,
            'scheduled_at': direct_award_bundle.scheduled_at.strftime('%Y-%m-%d %H:%M'),
            'badgeclass_description': badgeclass.description,
            'badgeclass_name': badgeclass.name,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_feedback_mail(current_user, message):
        template = 'email/feedback.html'
        email_vars = {
            'current_user': current_user,
            'date': datetime.datetime.now(datetime.timezone.utc),
            'environment': settings.DOMAIN,
            'message': message,
        }
        return render_to_string(template, email_vars)

    @staticmethod
    def create_email_validation_mail(code, user, badge, issuer):
        template = 'email/email_validation.html'
        email_vars = {'code': code, 'user': user, 'badge': badge, 'issuer': issuer}
        return render_to_string(template, email_vars)


def send_mail(subject, message, recipient_list=None, html_message=None, bcc=None):
    if settings.LOCAL_DEVELOPMENT_MODE:
        open_mail_in_browser(html_message)
    if html_message:
        html_with_inline_css = transform(html_message)
        msg = mail.EmailMessage(subject=subject, body=html_with_inline_css, from_email=None, to=recipient_list, bcc=bcc)
        msg.content_subtype = 'html'
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


def generate_image_url(image):
    if image.name:
        if getattr(settings, 'MEDIA_URL').startswith('http'):
            return default_storage.url(image.name)
        else:
            return getattr(settings, 'HTTP_ORIGIN') + default_storage.url(image.name)


def _decompression_bomb_check(image, max_pixels=Image.MAX_IMAGE_PIXELS):
    pixels = image.size[0] * image.size[1]
    return pixels > max_pixels


def add_watermark(uploaded_image, is_svg):
    text = 'DEMO'
    angle = 45
    opacity = 0.85
    absolute = pathlib.Path().absolute()
    font = f'{absolute}/apps/mainsite/arial.ttf'

    if is_svg:
        svg_buf = io.BytesIO()
        uploaded_image.file.seek(0)
        c = cairosvg.svg2png(file_obj=uploaded_image)
        svg_buf.write(c)
        img = Image.open(svg_buf)
    else:
        img = Image.open(uploaded_image)

    watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
    preferred_width = int(math.sqrt(int(math.pow(img.size[0], 2)) + int(math.pow(img.size[1], 2))))
    font_size = int(preferred_width / (len(text) + 1))
    n_font = ImageFont.truetype(font, font_size)
    left, top, right, bottom = n_font.getbbox(text)
    n_width = right - left
    n_height = bottom - top
    draw = ImageDraw.Draw(watermark, 'RGBA')
    draw.text(
        ((watermark.size[0] - n_width) / 2, (watermark.size[1] - n_height) / 2), text, font=n_font, fill=(220, 12, 12)
    )
    watermark = watermark.rotate(angle, Image.BICUBIC)
    alpha = watermark.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    watermark.putalpha(alpha)

    new_image = Image.composite(watermark, img, watermark)
    byte_string = io.BytesIO()
    new_image.save(byte_string, 'PNG')
    image_name = uploaded_image.name
    if is_svg:
        pattern = re.compile(r'\.svg', re.IGNORECASE)
        image_name = pattern.sub('.png', image_name)
    return InMemoryUploadedFile(byte_string, None, image_name, 'image/png', byte_string.getvalue().__len__(), None)


def resize_image(uploaded_image):
    try:
        f = open(uploaded_image.name, 'rb')
        image = Image.open(f)
        if _decompression_bomb_check(image):
            raise ValidationError('Invalid image')
    except IOError:
        return uploaded_image
    if image.format == 'PNG':
        max_square = getattr(settings, 'IMAGE_FIELD_MAX_PX', 400)
        smaller_than_canvas = image.width < max_square and image.height < max_square
        if smaller_than_canvas:
            max_square = image.width if image.width > image.height else image.height
        new_image = resize_contain(image, (max_square, max_square))
        byte_string = io.BytesIO()
        new_image.save(byte_string, 'PNG')
        return InMemoryUploadedFile(
            byte_string, None, uploaded_image.name, 'image/png', byte_string.getvalue().__len__(), None
        )


def scrub_svg_image(uploaded_image):
    MALICIOUS_SVG_TAGS = ['script']
    MALICIOUS_SVG_ATTRIBUTES = ['onload']
    SVG_NAMESPACE = 'http://www.w3.org/2000/svg'
    uploaded_image.file.seek(0)
    ET.register_namespace('', SVG_NAMESPACE)
    tree = ET.parse(uploaded_image.file)
    root = tree.getroot()

    # strip malicious tags
    elements_to_strip = []
    for tag_name in MALICIOUS_SVG_TAGS:
        elements_to_strip.extend(root.findall('{{{ns}}}{tag}'.format(ns=SVG_NAMESPACE, tag=tag_name)))
    for e in elements_to_strip:
        root.remove(e)

    # strip malicious attributes
    for el in tree.iter():
        for attrib_name in MALICIOUS_SVG_ATTRIBUTES:
            if attrib_name in el.attrib:
                del el.attrib[attrib_name]

    # write out scrubbed svg
    buf = io.BytesIO()
    tree.write(buf)
    return InMemoryUploadedFile(buf, 'image', uploaded_image.name, 'image/svg+xml', buf.getbuffer().nbytes, 'utf8')
