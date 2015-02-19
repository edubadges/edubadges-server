from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from models import EarnerNotification
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge
from badgeanalysis.serializers import BadgeSerializer


class EarnerNotificationSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=2048)
    email = serializers.CharField(max_length=254)
    badge = BadgeSerializer(required=False)

    def validate_url(self, value):
        if not value or value == '':
            raise ValidationError("Value is required.")
        if EarnerNotification.detect_existing(value):
            raise ValidationError(
                "The earner of this assertion has already been notified: " + value
            )
        return value

    def validate(self, data):
        if not data.get('badge'):
            try:
                badge, badge_is_new = OpenBadge.get_or_create(
                    recipient_input=data.get('email'),
                    badge_input=data.get('url'),
                    **{'create_only': ()}
                )
            except BadgeValidationError as e:
                raise ValidationError(
                    "Badge could not be validated: " + e.to_dict()['message']  # This error's likely that the earner email address != intended notification target
                )
            except Exception as e:
                raise ValidationError("Badge could not be validated: " + e.message)
            else:
                data['badge'] = badge
                return data

    def create(self):
        """
        Create the notification instance and send the email. You must run .is_valid() before calling .create()
        """
        if self.errors:
            raise ValidationError("Tried to create the notification with invalid input.")

        notification = EarnerNotification(
            url = self.data.get('url'),
            badge_id = self.data.get('badge').get('pk'),
            email = self.data.get('email')
        )

        try: 
            notification.send_email()
        except Exception as e:
            raise e
        else:
            notification.save()
            return notification
