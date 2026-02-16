import logging

from fcm_django.models import FCMDevice
from firebase_admin import messaging


logger = logging.getLogger(__name__)

def send_push_notification(user, title, body, data):
    devices = FCMDevice.objects.filter(user=user, active=True)
    if not devices:
        logger.info(f"No FCM devices found for user {user.id} ({user.entity_id})")
        return None

    message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
        )

    logger.info(f"Sending push to {devices.count()} devices for user {user.id} ({user.entity_id})")
    firebase_response = devices.send_message(message=message)

    batch_response = firebase_response.response
    if batch_response.failure_count > 0:
        logger.warning(
            f"{batch_response.failure_count} push notifications failed. "
            f"Deactivated devices: {firebase_response.deactivated_registration_ids}"
        )
    else:
        logger.info(f"All {batch_response.success_count} push notifications sent successfully")

    return firebase_response
