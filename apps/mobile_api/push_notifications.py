import logging

from fcm_django.models import FCMDevice
from firebase_admin import messaging
from firebase_admin.messaging import APNSConfig, APNSPayload, Aps, AndroidConfig, AndroidNotification
from google.auth.exceptions import DefaultCredentialsError


logger = logging.getLogger('Badgr.Debug')

def send_push_notification(user, title, body, data, badge_count):
    if not user:
        logger.info(f"No user found, skipping push notification.")
        return None
    devices = FCMDevice.objects.filter(user=user, active=True)
    if not devices:
        logger.info(f"No FCM devices found for user {user.id} ({user.entity_id})")
        return None

    # Make sure only str data is added to the Message
    data = {k: str(v) for k, v in data.items()}

    message = messaging.Message(
        notification=messaging.Notification(title=title, body=body),
        data=data,
        # Apple Specific Badge Setup
        apns=APNSConfig(
            payload=APNSPayload(
                aps=Aps(
                    badge=badge_count,
                ),
            ),
        ),
        # Android Specific Badge Setup
        android=AndroidConfig(
            notification=AndroidNotification(
                notification_count=badge_count,
                tag="user_unclaimed_awards",
            ),
        ),
    )

    logger.info(f"Sending push to {devices.count()} devices for user {user.id} ({user.entity_id})")
    try:
        firebase_response = devices.send_message(message=message)
    except DefaultCredentialsError as e:
        logger.error(f"Cannot send FCM push: credentials file missing or unreadable. {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to send push: {e}")
        return None
    else:
        batch_response = firebase_response.response
        if batch_response.failure_count > 0:
            logger.warning(
                f"{batch_response.failure_count} push notifications failed. "
                f"Deactivated devices: {firebase_response.deactivated_registration_ids}"
            )
        else:
            logger.info(f"All {batch_response.success_count} push notifications sent successfully")

        return firebase_response
