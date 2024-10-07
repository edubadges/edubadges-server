import django.dispatch
import logging
import uuid
from django.dispatch import receiver
from django.db import models


class ValidatedNameAuditTrail(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    action_datetime = models.DateTimeField(auto_now=True)
    user = models.CharField(max_length=254, blank=True)
    old_validated_name = models.CharField(max_length=255, blank=True)
    new_validated_name = models.CharField(max_length=255, blank=True)


# Signals doc: https://docs.djangoproject.com/en/3.2/topics/signals/
val_name_audit_trail_signal = django.dispatch.Signal(
    providing_args=['user', 'old_validated_name', 'new_validated_name']
)  # creates a custom signal and specifies the args required.

logger = logging.getLogger(__name__)


@receiver(val_name_audit_trail_signal)
def new_val_name_audit_trail(sender, user, old_validated_name, new_validated_name, **kwargs):
    try:
        audit_trail = ValidatedNameAuditTrail.objects.create(
            user=user,
            old_validated_name=old_validated_name,
            new_validated_name=new_validated_name,
        )
        logger.info(f'val_name_audit_trail created {audit_trail.id}  for user {audit_trail.user}')
    except Exception as e:
        logger.error('val_name_audit_trail error: %s' % (e))
