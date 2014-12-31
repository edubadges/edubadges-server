from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from models import EarnerNotification
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge


class EarnerNotificationSerializer(serializers.Serializer):
    url = serializers.CharField(max_length=2048)
    email = serializers.CharField(max_length=254)

    def create(self, validated_data):
        if EarnerNotification.detect_existing(validated_data.get('url')):
            raise ValidationError(
                "The earner of this assertion has already been notified: " + validated_data.get('url')
            )
        else:
            notification = EarnerNotification(**validated_data)
            # notification.save(commit=False)

            try:
                notification.badge = OpenBadge(
                    recipient_input=validated_data.get('email'),
                    badge_input=validated_data.get('url')
                )
                notification.badge.save()
            except BadgeValidationError as e:
                raise ValidationError(
                    e.to_dict()['message']  # This error's likely that the earner email address != intended notification target
                )
            else:
                try: 
                    notification.send_email()
                except Exception as e:
                    raise e
                else:
                    notification.save()
                    return notification
