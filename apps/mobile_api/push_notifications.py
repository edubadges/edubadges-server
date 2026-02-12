from fcm_django.models import FCMDevice
from firebase_admin import messaging


def send_push_notification(user, title, body, data):
    devices = FCMDevice.objects.filter(user=user, active=True)
    if not devices:
        return None

    message = messaging.Message(
            notification=messaging.Notification(title=title, body=body),
            data=data,
        )

    firebase_response = devices.send_message(message=message)
    return firebase_response
