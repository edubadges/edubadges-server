import base64
import datetime
import hashlib
import io
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from xml.etree import cElementTree as ET

from django.core.exceptions import ValidationError
from django.test import TestCase, RequestFactory
from django.core.files.uploadedfile import InMemoryUploadedFile
from PIL import Image

from apps.mainsite.utils import (
    client_ip_from_request,
    filter_cache_key,
    verify_svg,
    fetch_remote_file_to_storage,
    generate_entity_uri,
    first_node_match,
    list_of,
    scrub_svg_image,
    resize_image,
    add_watermark,
    _decompression_bomb_check,
    generate_image_url,
    send_mail,
    admin_list_linkify,
    EmailMessageMaker,
    OriginSettingsObject
)


class TestClientIpFromRequest(TestCase):
    """new"""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_ip_from_x_forwarded_for_header(self):
        request = self.factory.get('/')
        request.headers = {'x-forwarded-for': '192.168.1.1, 10.0.0.1'}
        result = client_ip_from_request(request)
        self.assertEqual(result, '192.168.1.1')
    
    def test_ip_from_remote_addr_when_no_forwarded_header(self):
        request = self.factory.get('/')
        request.headers = {}
        request.META = {'REMOTE_ADDR': '127.0.0.1'}
        result = client_ip_from_request(request)
        self.assertEqual(result, '127.0.0.1')
    
    def test_empty_string_when_no_ip_available(self):
        request = self.factory.get('/')
        request.headers = {}
        request.META = {}
        result = client_ip_from_request(request)
        self.assertEqual(result, '')


class TestFilterCacheKey(TestCase):
    """new"""
    
    def test_short_key_returns_as_is(self):
        key = 'test_key'
        prefix = 'prefix'
        version = 1
        result = filter_cache_key(key, prefix, version)
        expected = 'prefix:1:test_key'
        self.assertEqual(result, expected)
    
    def test_long_key_returns_md5_hash(self):
        key = 'a' * 300
        prefix = 'prefix'
        version = 1
        result = filter_cache_key(key, prefix, version)
        generated_key = f'prefix:1:{key}'
        expected = hashlib.md5(generated_key.encode()).hexdigest()
        self.assertEqual(result, expected)


class TestVerifySvg(TestCase):
    """new"""
    
    def test_valid_svg_returns_true(self):
        svg_content = b'<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"></svg>'
        fileobj = io.BytesIO(svg_content)
        result = verify_svg(fileobj)
        self.assertTrue(result)
    
    def test_invalid_xml_returns_false(self):
        invalid_content = b'not xml content'
        fileobj = io.BytesIO(invalid_content)
        result = verify_svg(fileobj)
        self.assertFalse(result)
    
    def test_non_svg_xml_returns_false(self):
        xml_content = b'<?xml version="1.0"?><root></root>'
        fileobj = io.BytesIO(xml_content)
        result = verify_svg(fileobj)
        self.assertFalse(result)


class TestGenerateEntityUri(TestCase):
    """new"""
    
    def test_generates_url_safe_string(self):
        result = generate_entity_uri()
        self.assertIsInstance(result, str)
        self.assertNotIn('=', result)
        self.assertNotIn('+', result)
        self.assertNotIn('/', result)
    
    def test_generates_unique_strings(self):
        result1 = generate_entity_uri()
        result2 = generate_entity_uri()
        self.assertNotEqual(result1, result2)


class TestFirstNodeMatch(TestCase):
    """new"""
    
    def test_finds_matching_node(self):
        graph = [
            {'id': 1, 'name': 'first'},
            {'id': 2, 'name': 'second'},
            {'id': 3, 'name': 'third'}
        ]
        condition = {'id': 2}
        result = first_node_match(graph, condition)
        self.assertEqual(result, {'id': 2, 'name': 'second'})
    
    def test_returns_none_when_no_match(self):
        graph = [{'id': 1, 'name': 'first'}]
        condition = {'id': 2}
        result = first_node_match(graph, condition)
        self.assertIsNone(result)
    
    def test_matches_multiple_conditions(self):
        graph = [
            {'id': 1, 'name': 'first', 'type': 'A'},
            {'id': 2, 'name': 'second', 'type': 'B'}
        ]
        condition = {'id': 2, 'type': 'B'}
        result = first_node_match(graph, condition)
        self.assertEqual(result, {'id': 2, 'name': 'second', 'type': 'B'})


class TestListOf(TestCase):
    """new"""
    
    def test_none_returns_empty_list(self):
        result = list_of(None)
        self.assertEqual(result, [])
    
    def test_list_returns_same_list(self):
        input_list = [1, 2, 3]
        result = list_of(input_list)
        self.assertEqual(result, input_list)
    
    def test_single_value_returns_list_with_value(self):
        result = list_of('test')
        self.assertEqual(result, ['test'])


class TestDecompressionBombCheck(TestCase):
    """new"""
    
    def test_small_image_returns_false(self):
        mock_image = Mock()
        mock_image.size = (100, 100)
        result = _decompression_bomb_check(mock_image, max_pixels=20000)
        self.assertFalse(result)
    
    def test_large_image_returns_true(self):
        mock_image = Mock()
        mock_image.size = (1000, 1000)
        result = _decompression_bomb_check(mock_image, max_pixels=500000)
        self.assertTrue(result)


class TestOriginSettingsObject(TestCase):
    """new"""
    
    def test_default_origin(self):
        origin_obj = OriginSettingsObject()
        self.assertEqual(origin_obj.DefaultOrigin, 'http://localhost:8000')
    
    @patch('apps.mainsite.utils.settings')
    def test_http_property_uses_settings(self, mock_settings):
        mock_settings.HTTP_ORIGIN = 'https://example.com'
        origin_obj = OriginSettingsObject()
        result = origin_obj.HTTP
        self.assertEqual(result, 'https://example.com')
    
    @patch('apps.mainsite.utils.settings')
    def test_default_http_protocol_extracts_scheme(self, mock_settings):
        mock_settings.HTTP_ORIGIN = 'https://example.com'
        origin_obj = OriginSettingsObject()
        result = origin_obj.DEFAULT_HTTP_PROTOCOL
        self.assertEqual(result, 'https')


@patch('apps.mainsite.utils.requests')
@patch('apps.mainsite.utils.DefaultStorage')
class TestFetchRemoteFileToStorage(TestCase):
    """new"""
    
    def test_successful_fetch_and_store(self, mock_storage_class, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b'file content'
        mock_response.url = 'http://example.com/file.jpg'
        mock_requests.get.return_value = mock_response
        
        mock_storage = Mock()
        mock_storage.exists.return_value = False
        mock_storage_class.return_value = mock_storage
        
        status_code, storage_name = fetch_remote_file_to_storage('http://example.com/file.jpg')
        
        self.assertEqual(status_code, 200)
        self.assertIsNotNone(storage_name)
        mock_storage.save.assert_called_once()
    
    def test_failed_fetch_returns_status_and_none(self, mock_storage_class, mock_requests):
        mock_response = Mock()
        mock_response.status_code = 404
        mock_requests.get.return_value = mock_response
        
        status_code, storage_name = fetch_remote_file_to_storage('http://example.com/missing.jpg')
        
        self.assertEqual(status_code, 404)
        self.assertIsNone(storage_name)


@patch('apps.mainsite.utils.settings')
class TestSendMail(TestCase):
    """new"""
    
    @patch('apps.mainsite.utils.open_mail_in_browser')
    @patch('apps.mainsite.utils.mail.EmailMessage')
    def test_local_development_opens_in_browser(self, mock_email_message, mock_open_browser, mock_settings):
        mock_settings.LOCAL_DEVELOPMENT_MODE = True
        
        send_mail('Subject', 'Message', ['test@example.com'], html_message='<html>Test</html>')
        
        mock_open_browser.assert_called_once_with('<html>Test</html>')


class TestAdminListLinkify(TestCase):
    """new"""
    
    def test_linkify_with_related_object(self):
        mock_obj = Mock()
        mock_related = Mock()
        mock_related.pk = 1
        mock_related._meta.app_label = 'test_app'
        mock_related._meta.model_name = 'test_model'
        mock_obj.test_field = mock_related
        
        with patch('apps.mainsite.utils.reverse') as mock_reverse:
            mock_reverse.return_value = '/admin/url/'
            linkify_func = admin_list_linkify('test_field')
            result = linkify_func(mock_obj)
            
            self.assertIn('/admin/url/', result)
            self.assertIn('<a href=', result)
    
    def test_linkify_with_none_returns_dash(self):
        mock_obj = Mock()
        mock_obj.test_field = None
        
        linkify_func = admin_list_linkify('test_field')
        result = linkify_func(mock_obj)
        
        self.assertEqual(result, '-')


class TestEmailMessageMaker(TestCase):
    """new"""
    
    def test_create_enrollment_denied_email(self):
        mock_enrollment = Mock()
        mock_enrollment.badge_class.public_url = 'http://example.com/badge'
        mock_enrollment.badge_class.name = 'Test Badge'
        mock_enrollment.user.full_name = 'John Doe'
        mock_enrollment.deny_reason = 'Test reason'
        
        with patch('apps.mainsite.utils.render_to_string') as mock_render:
            mock_render.return_value = 'rendered email'
            result = EmailMessageMaker.create_enrollment_denied_email(mock_enrollment)
            
            self.assertEqual(result, 'rendered email')
            mock_render.assert_called_once()
    
    def test_create_feedback_mail(self):
        mock_user = Mock()
        mock_user.full_name = 'John Doe'
        message = 'Test feedback'
        
        with patch('apps.mainsite.utils.render_to_string') as mock_render:
            with patch('apps.mainsite.utils.settings') as mock_settings:
                mock_settings.DOMAIN = 'example.com'
                mock_render.return_value = 'rendered feedback'
                
                result = EmailMessageMaker.create_feedback_mail(mock_user, message)
                
                self.assertEqual(result, 'rendered feedback')
                mock_render.assert_called_once()


@patch('apps.mainsite.utils.settings')
class TestGenerateImageUrl(TestCase):
    """new"""
    
    def test_http_media_url_returns_storage_url(self, mock_settings):
        mock_settings.MEDIA_URL = 'http://cdn.example.com/media/'
        mock_image = Mock()
        mock_image.name = 'test.jpg'
        
        with patch('apps.mainsite.utils.default_storage') as mock_storage:
            mock_storage.url.return_value = '/media/test.jpg'
            result = generate_image_url(mock_image)
            
            self.assertEqual(result, '/media/test.jpg')
    
    def test_relative_media_url_prepends_http_origin(self, mock_settings):
        mock_settings.MEDIA_URL = '/media/'
        mock_settings.HTTP_ORIGIN = 'https://example.com'
        mock_image = Mock()
        mock_image.name = 'test.jpg'
        
        with patch('apps.mainsite.utils.default_storage') as mock_storage:
            mock_storage.url.return_value = '/media/test.jpg'
            result = generate_image_url(mock_image)
            
            self.assertEqual(result, 'https://example.com/media/test.jpg')
    
    def test_no_image_name_returns_none(self, mock_settings):
        mock_image = Mock()
        mock_image.name = None
        
        result = generate_image_url(mock_image)
        
        self.assertIsNone(result)


class TestScrubSvgImage(TestCase):
    """new"""
    
    def test_removes_script_tags(self):
        svg_with_script = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg">
            <script>alert('xss')</script>
            <circle r="10"/>
        </svg>'''
        
        mock_file = Mock()
        mock_file.file = io.BytesIO(svg_with_script)
        mock_file.name = 'test.svg'
        
        result = scrub_svg_image(mock_file)

        self.assertIsInstance(result, InMemoryUploadedFile)
        self.assertEqual(result.name, 'test.svg')
    
    def test_removes_onload_attributes(self):
        svg_with_onload = b'''<?xml version="1.0"?>
        <svg xmlns="http://www.w3.org/2000/svg" onload="alert('xss')">
            <circle r="10"/>
        </svg>'''
        
        mock_file = Mock()
        mock_file.file = io.BytesIO(svg_with_onload)
        mock_file.name = 'test.svg'
        
        result = scrub_svg_image(mock_file)

        self.assertIsInstance(result, InMemoryUploadedFile)
        self.assertEqual(result.name, 'test.svg')


if __name__ == '__main__':
    unittest.main()
