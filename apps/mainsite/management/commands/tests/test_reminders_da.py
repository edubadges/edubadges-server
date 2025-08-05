from datetime import timedelta
from io import StringIO
from unittest.mock import Mock, patch

from django.core import mail
from django.core.management import call_command
from django.core.management.base import OutputWrapper
from django.utils import timezone
from mainsite.tests import BadgrTestCase


class TestDirectAwardsReminderHandler(BadgrTestCase):
    def setUp(self):
        super().setUp()
        self.handler = Mock()
        self.handler.stdout = Mock()
        self.handler.stdout.write = Mock()

        # Mock the actual handle method
        from apps.mainsite.management.commands.reminders_direct_awards import Command

        self.command_instance = Command()
        captured_output = StringIO()
        self.output_wrapper = OutputWrapper(captured_output)
        self.command_instance.stdout = self.output_wrapper

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

        # Setup mocks
        mock_now = timezone.now()
        mock_timezone.now.return_value = mock_now
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '14, 42'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        now = timezone.now()

        teacher1 = self.setup_teacher(authenticate=False)
        issuer = self.setup_issuer(teacher1)
        badgeclass = self.setup_badgeclass(issuer)

        da1 = self.setup_direct_award(
            badgeclass=badgeclass, created_by=teacher1, eppn='some_eppn', expiration_date=now + timedelta(days=40)
        )
        da2 = self.setup_direct_award(
            badgeclass=badgeclass,
            created_by=teacher1,
            eppn='some_eppn_2',
            expiration_date=now + timedelta(days=12),
            reminders=1,
        )
        da3 = self.setup_direct_award(
            badgeclass=badgeclass,
            created_by=teacher1,
            eppn='some_eppn_3',
            expiration_date=now + timedelta(days=-1),
            reminders=2,
        )

        # Execute the method
        self.command_instance.handle()

        # Verify database connections are closed
        mock_connections.close_all.assert_called_once()

        # Verify logger setup
        mock_logging.getLogger.assert_called_with('Badgr.Debug')
        mock_logger.info.assert_any_call('Running reminders_direct_awards')
        mock_logger.info.assert_any_call('Sending 1 reminder emails for reminder: 0, threshold: 42')
        mock_logger.info.assert_any_call('Sending 1 reminder emails for reminder: 1, threshold: 14')

        # Assert email was sent
        self.assertEqual(len(mail.outbox), 3)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Reminder: your edubadge will expire')
        email = mail.outbox[2]
        self.assertEqual(email.subject, 'Your edubadge has been deleted')

    @patch('apps.mainsite.management.commands.reminders_direct_awards.connections')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.logging')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.timezone')
    @patch('apps.mainsite.management.commands.reminders_direct_awards.settings')
    def test_handle_successful_execution_one_da(
        self,
        mock_settings,
        mock_timezone,
        mock_logging,
        mock_connections,
    ):
        # Clear any existing emails
        mail.outbox = []

        # Setup mocks
        mock_now = timezone.now()
        mock_timezone.now.return_value = mock_now
        mock_settings.EXPIRY_DIRECT_AWARDS_REMINDER_THRESHOLD_DAYS = '14, 42'

        mock_logger = Mock()
        mock_logging.getLogger.return_value = mock_logger

        now = timezone.now()

        teacher1 = self.setup_teacher(authenticate=False)
        issuer = self.setup_issuer(teacher1)
        badgeclass = self.setup_badgeclass(issuer)

        self.setup_direct_award(
            badgeclass=badgeclass, created_by=teacher1, eppn='some_eppn', expiration_date=now + timedelta(days=41)
        )
        self.setup_direct_award(
            badgeclass=badgeclass, created_by=teacher1, eppn='some_eppn2', expiration_date=now + timedelta(days=42)
        )

        # Execute the method
        self.command_instance.handle()

        # Verify database connections are closed
        mock_connections.close_all.assert_called_once()

        # Verify logger setup
        mock_logging.getLogger.assert_called_with('Badgr.Debug')
        mock_logger.info.assert_any_call('Running reminders_direct_awards')
        mock_logger.info.assert_any_call('Sending 1 reminder emails for reminder: 0, threshold: 42')
        mock_logger.info.assert_any_call('Sending 0 reminder emails for reminder: 1, threshold: 14')

        # Assert email was sent
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, 'Reminder: your edubadge will expire')

    @classmethod
    def tearDownClass(cls):
        call_command('flush', interactive=False)
        super().tearDownClass()
