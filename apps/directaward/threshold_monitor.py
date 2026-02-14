import datetime
import logging
from django.db.models import Count, Q
from django.core.management.base import BaseCommand
from django.conf import settings
from directaward.models import DirectAward, DirectAwardBundle
from mainsite.utils import send_mail

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check for suspicious direct award activity and notify admins'

    def handle(self, *args, **options):
        self.check_threshold_violations()
        self.check_pending_approvals()

    def check_threshold_violations(self):
        """Check for potential threshold violations in direct award creation"""
        threshold = getattr(settings, 'DIRECT_AWARD_THRESHOLD_PER_HOUR', 10)
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=1)

        # Find creators who have created many direct awards recently
        suspicious_creators = (
            DirectAward.objects.filter(created_at__gte=time_threshold)
            .values('created_by__email')
            .annotate(count=Count('id'))
            .filter(count__gte=threshold)
        )

        for creator in suspicious_creators:
            self.notify_admins(
                f'Suspicious direct award activity detected',
                f'User {creator["created_by__email"]} has created {creator["count"]} direct awards in the last hour.',
            )

    def check_pending_approvals(self):
        """Check for pending approvals that need attention"""
        pending_count = DirectAward.objects.filter(status=DirectAward.STATUS_PENDING_APPROVAL).count()

        if pending_count > 0:
            self.notify_admins(
                f'{pending_count} direct awards pending approval',
                f'There are {pending_count} direct awards waiting for administrative approval.',
            )

    def notify_admins(self, subject, message):
        """Send notification to institution admins"""
        # In a real implementation, you would get admin emails from your user model
        # For now, we'll use a setting or log the message
        admin_emails = getattr(settings, 'ADMIN_NOTIFICATION_EMAILS', [])

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                recipient_list=admin_emails,
            )
        else:
            logger.warning(f'Admin notification would be sent: {subject} - {message}')


class ThresholdCheckResult:
    """Result of threshold checking"""

    def __init__(self, passed, violations=None):
        self.passed = passed
        self.violations = violations or {}


class DirectAwardThresholdMonitor:
    """Monitor for suspicious direct award activity with real-time checking"""

    def __init__(self):
        # Default thresholds - can be overridden by institution settings
        self.thresholds = {
            'MAX_PER_HOUR': getattr(settings, 'DIRECT_AWARD_MAX_PER_HOUR', 10),
            'MAX_PER_DAY': getattr(settings, 'DIRECT_AWARD_MAX_PER_DAY', 50),
            'MAX_SAME_RECIPIENT': getattr(settings, 'DIRECT_AWARD_MAX_SAME_RECIPIENT', 3),
            'MAX_SAME_BADGECLASS': getattr(settings, 'DIRECT_AWARD_MAX_SAME_BADGECLASS', 5),
        }

    def check_award(self, direct_award):
        """Check if a direct award passes all threshold checks"""
        violations = {}

        # Check hourly limit for creator
        if not self._check_creator_hourly_limit(direct_award):
            violations['hourly_limit'] = {
                'threshold': self.thresholds['MAX_PER_HOUR'],
                'actual': self._get_creator_recent_count(direct_award, hours=1),
            }

        # Check daily limit for creator
        if not self._check_creator_daily_limit(direct_award):
            violations['daily_limit'] = {
                'threshold': self.thresholds['MAX_PER_DAY'],
                'actual': self._get_creator_recent_count(direct_award, hours=24),
            }

        # Check same recipient limit
        if not self._check_same_recipient_limit(direct_award):
            violations['same_recipient'] = {
                'threshold': self.thresholds['MAX_SAME_RECIPIENT'],
                'actual': self._get_same_recipient_count(direct_award),
            }

        # Check same badgeclass limit
        if not self._check_same_badgeclass_limit(direct_award):
            violations['same_badgeclass'] = {
                'threshold': self.thresholds['MAX_SAME_BADGECLASS'],
                'actual': self._get_same_badgeclass_count(direct_award),
            }

        if violations:
            logger.warning(f'Threshold violations detected for direct award {direct_award.id}: {violations}')
            return ThresholdCheckResult(passed=False, violations=violations)

        return ThresholdCheckResult(passed=True)

    def _check_creator_hourly_limit(self, direct_award):
        """Check if creator is within hourly limit"""
        count = self._get_creator_recent_count(direct_award, hours=1)
        return count < self.thresholds['MAX_PER_HOUR']

    def _check_creator_daily_limit(self, direct_award):
        """Check if creator is within daily limit"""
        count = self._get_creator_recent_count(direct_award, hours=24)
        return count < self.thresholds['MAX_PER_DAY']

    def _check_same_recipient_limit(self, direct_award):
        """Check if same recipient is getting too many awards"""
        count = self._get_same_recipient_count(direct_award)
        return count < self.thresholds['MAX_SAME_RECIPIENT']

    def _check_same_badgeclass_limit(self, direct_award):
        """Check if same badgeclass is being awarded too much"""
        count = self._get_same_badgeclass_count(direct_award)
        return count < self.thresholds['MAX_SAME_BADGECLASS']

    def _get_creator_recent_count(self, direct_award, hours=1):
        """Get count of recent awards by same creator"""
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=hours)
        return DirectAward.objects.filter(created_by=direct_award.created_by, created_at__gte=time_threshold).count()

    def _get_same_recipient_count(self, direct_award):
        """Get count of recent awards to same recipient"""
        time_threshold = datetime.datetime.now() - datetime.timedelta(days=1)
        return DirectAward.objects.filter(
            Q(eppn=direct_award.eppn) | Q(recipient_email=direct_award.recipient_email), created_at__gte=time_threshold
        ).count()

    def _get_same_badgeclass_count(self, direct_award):
        """Get count of recent awards for same badgeclass"""
        time_threshold = datetime.datetime.now() - datetime.timedelta(hours=1)
        return DirectAward.objects.filter(
            badgeclass=direct_award.badgeclass, created_by=direct_award.created_by, created_at__gte=time_threshold
        ).count()
