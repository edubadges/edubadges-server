import logging

import django.dispatch
from django.dispatch import receiver

from .models import DirectAwardAuditTrail

# Signals doc: https://docs.djangoproject.com/en/4.2/topics/signals/
audit_trail_signal = django.dispatch.Signal()  # creates a custom signal and specifies the args required.

logger = logging.getLogger(__name__)


# helper func that gets the client ip
def get_client_ip(request):
    x_forwarded_for = request.headers.get('x-forwarded-for')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@receiver(audit_trail_signal)
def direct_award_audit_trail(sender, user, request, direct_award_id, badgeclass_id, method, summary, **kwargs):
    try:
        user_agent_info = (request.headers.get('user-agent', '<unknown>')[:255],)
        audit_trail = DirectAwardAuditTrail.objects.create(
            user=user,
            user_agent_info=user_agent_info,
            login_IP=get_client_ip(request),
            action=method,
            change_summary=summary,
            direct_award_id=direct_award_id,
            badgeclass_id=badgeclass_id,
        )
        logger.info(
            f'direct_award_audit_trail created {audit_trail.id}  for user {audit_trail.user} and directaward {audit_trail.direct_award_id}'
        )
    except Exception as e:
        logger.error('direct_award_audit_trail request: %s, error: %s' % (request, e))
