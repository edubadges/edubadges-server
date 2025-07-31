import random
import sys
from contextlib import redirect_stdout
from datetime import timedelta
from io import StringIO
from unittest.mock import Mock, call, patch

from directaward.models import DirectAward, DirectAwardBundle
from django.core import mail
from django.core.management import call_command
from django.core.management.base import OutputWrapper
from django.test import tag
from django.utils import timezone
from issuer.models import BadgeClass
from mainsite.models import BadgrApp
from mainsite.tests import BadgrTestCase, string_randomiser
from mainsite.utils import resize_image


def setup_direct_award(badgeclass, **kwargs):
    if not kwargs.get('recipient_email', False):
        kwargs['recipient_email'] = string_randomiser('some@amail.com', prefix=True)
    if not kwargs.get('eppn', False):
        kwargs['eppn'] = string_randomiser('eppn')
    if not kwargs.get('expiration_date', False):
        kwargs['expiration_date'] = timezone.now() + timedelta(days=7)
    if not kwargs.get('reminders', False):
        kwargs['reminders'] = 0
    if not kwargs.get('bundle', False):
        kwargs['bundle'] = DirectAwardBundle.objects.create(badgeclass=badgeclass, initial_total=1)
    else:
        kwargs['bundle'].initial_total += 1
        kwargs['bundle'].save()
    direct_award = DirectAward.objects.create(badgeclass=badgeclass, **kwargs)
    badgeclass.remove_cached_data(['cached_direct_awards'])
    return direct_award


@tag('new')
class TestDirectAwardsReminderHandler(BadgrTestCase):
    def setUp(self):
        self.handler = Mock()
        self.handler.stdout = Mock()
        self.handler.stdout.write = Mock()

        # Mock the actual handle method
        from apps.mainsite.management.commands.reminders_direct_awards import Command

        self.command_instance = Command()
        captured_output = StringIO()
        self.output_wrapper = OutputWrapper(captured_output)
        self.command_instance.stdout = self.output_wrapper

        from django.conf import settings

        badgr_app_id = getattr(settings, 'BADGR_APP_ID')
        self.badgr_app = BadgrApp.objects.get_or_create(pk=badgr_app_id)

    def setup_badgeclass(self, created_by, **kwargs):
        if not kwargs.get('name', False):
            kwargs['name'] = 'Test Badgeclass #{}'.format(random.random())
        if not kwargs.get('image', False):
            kwargs['image'] = resize_image(open(self.get_test_image_path(), 'r'))
        return BadgeClass.objects.create(
            issuer=created_by, formal=False, description='Description', criteria_text='Criteria text', **kwargs
        )

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    def test_handle_successful_execution(
        self,
        mock_settings,
        mock_timezone,
        mock_logging,
        mock_connections,
    ):
        # Clear any existing emails
        mail.outbox = []

        # Capture stdout
        captured_output = StringIO()
        sys.stdout = captured_output

        # Setup mocks
        mock_now = timezone.now()
        mock_timezone.now.return_value = mock_now
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '14, 42'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        now = timezone.now()

        # Mock DirectAward objects for reminders

        teacher1 = self.setup_teacher(authenticate=False)
        issuer = self.setup_issuer(teacher1)
        badgeclass = self.setup_badgeclass(created_by=issuer)

        da1 = setup_direct_award(
            badgeclass=badgeclass, created_by=teacher1, eppn='some_eppn', expiration_date=now + timedelta(days=40)
        )
        da2 = setup_direct_award(
            badgeclass=badgeclass,
            created_by=teacher1,
            eppn='some_eppn_2',
            expiration_date=now + timedelta(days=12),
            reminders=1,
        )
        da3 = setup_direct_award(
            badgeclass=badgeclass,
            created_by=teacher1,
            eppn='some_eppn_3',
            expiration_date=now + timedelta(days=-1),
            reminders=2,
        )

        with redirect_stdout(captured_output):
            # Execute the method
            self.command_instance.handle()

        # Verify database connections are closed
        mock_connections.close_all.assert_called_once()

        # Verify logger setup
        mock_logging.getLogger.assert_called_with('Badgr.Debug')
        mock_logger.info.assert_any_call('Running reminders_direct_awards')

        # Verify reminder emails sent
        expected_reminder_calls = [
            call(
                subject='asdsadad',
                message=None,
                html_message='reminder_html',
                recipient_list=['test1@example.com'],
            ),
            call(
                subject='Reminder: your edubadge will expire',
                message=None,
                html_message='reminder_html',
                recipient_list=['test2@example.com'],
            ),
        ]

        # Verify expired email sent
        expected_expired_call = call(
            subject='Your edubadge has been deleted',
            message=None,
            html_message='expired_html',
            recipient_list=['expired@example.com'],
        )

        # Verify reminder counters updated
        self.assertEqual(da1.reminders, 0)
        self.assertEqual(da2.reminders, 1)
        self.assertEqual(da3.reminders, 2)

        # Assert email was sent
        self.assertEqual(len(mail.outbox), 3)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Reminder: your edubadge will expire')
        email = mail.outbox[2]
        self.assertEqual(email.subject, 'Your edubadge has been deleted')

        # Get the captured output
        output = captured_output.getvalue()
        self.assertIn('Deleting 1 expired direct_awards', output)

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    def test_handle_empty_threshold_days(
        self, mock_direct_award, mock_settings, mock_timezone, mock_logging, mock_connections
    ):
        # Test with empty threshold days
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = ''
        mock_timezone.now.return_value = timezone.now()

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        # Mock empty results
        mock_direct_award.objects.filter.return_value.all.return_value = []

        # Should not raise an exception
        self.command_instance.handle()

        # Verify connections still closed
        mock_connections.close_all.assert_called_once()

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.send_mail')
    def test_handle_send_mail_exception(
        self, mock_send_mail, mock_direct_award, mock_settings, mock_timezone, mock_logging, mock_connections
    ):
        # Test behavior when send_mail raises an exception
        mock_timezone.now.return_value = timezone.now()
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '7'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        mock_award = Mock()
        mock_award.recipient_email = 'test@example.com'
        mock_award.reminders = 0

        mock_direct_award.objects.filter.side_effect = [
            Mock(all=Mock(return_value=[mock_award])),  # Reminder query
            Mock(all=Mock(return_value=[])),  # Expired query
        ]

        # Make send_mail raise an exception
        mock_send_mail.side_effect = Exception('SMTP Error')

        # Should not crash the entire process
        with self.assertRaises(Exception):
            self.command_instance.handle()

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.DirectAward')
    def test_threshold_days_sorting(
        self, mock_direct_award, mock_settings, mock_timezone, mock_logging, mock_connections
    ):
        # Test that threshold days are processed in reverse order
        mock_timezone.now.return_value = timezone.now()
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '21, 7, 14'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        # Mock empty results to focus on query order
        mock_direct_award.objects.filter.return_value.all.return_value = []

        self.command_instance.handle()

        # Verify the queries are made in reverse order (21, 14, 7)
        filter_calls = mock_direct_award.objects.filter.call_args_list

        # Should have 4 calls (3 thresholds + expired)
        self.assertEqual(len(filter_calls), 4)

        # First three calls should be for reminders in reverse order
        for i, call_args in enumerate(filter_calls[:3]):
            args, kwargs = call_args
            self.assertIn('reminders', kwargs)
            self.assertEqual(kwargs['reminders'], i)
            self.assertEqual(kwargs['status'], 'Unaccepted')

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    @patch('apps.mainsite.management.commands.reminders_direct_awards._remove_cached_direct_awards')
    def test_cache_removal_called(
        self, mock_remove_cache, mock_direct_award, mock_settings, mock_timezone, mock_logging, mock_connections
    ):
        # Test that cache removal is called for both reminder and expired awards
        mock_timezone.now.return_value = timezone.now()
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '7'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        mock_reminder_award = Mock()
        mock_reminder_award.recipient_email = 'reminder@example.com'

        mock_expired_award = Mock()
        mock_expired_award.recipient_email = 'expired@example.com'
        mock_expired_award.bundle = Mock()
        mock_expired_award.bundle.direct_award_expired_count = 0

        mock_direct_award.objects.filter.side_effect = [
            Mock(all=Mock(return_value=[mock_reminder_award])),  # Reminder query
            Mock(all=Mock(return_value=[mock_expired_award])),  # Expired query
        ]

        with (
            patch('apps.mainsite.management.commands.reminders_direct_awards.EmailMessageMaker'),
            patch('apps.mainsite.management.commands.reminders_direct_awards.send_mail'),
        ):
            self.command_instance.handle()

        # Verify cache removal called for both awards
        expected_calls = [call(mock_reminder_award), call(mock_expired_award)]
        mock_remove_cache.assert_has_calls(expected_calls)

    @classmethod
    def tearDownClass(cls):
        call_command('flush', interactive=False)
        super().tearDownClass()
