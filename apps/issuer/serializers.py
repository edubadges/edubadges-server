from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from models import EarnerNotification, Issuer, IssuerBadgeClass, IssuerAssertion
from badgeanalysis.validation_messages import BadgeValidationError
from badgeanalysis.models import OpenBadge
from badgeanalysis.serializers import BadgeSerializer
from mainsite.serializers import WritableJSONField
import utils
import badgeanalysis.utils

class AbstractBadgeObjectSerializer(serializers.Serializer):
    created_at = serializers.DateTimeField(read_only=True)
    created_by = serializers.HyperlinkedRelatedField(view_name='user_detail', lookup_field='username', read_only=True)


class IssuerSerializer(AbstractBadgeObjectSerializer):
    badge_object = WritableJSONField(max_length=16384, read_only=True, required=False)
    name = serializers.CharField(max_length=1024)
    slug = serializers.CharField(max_length=255, allow_blank=True)
    image = serializers.ImageField(allow_empty_file=False, use_url=True, required=False) 

    owner = serializers.HyperlinkedRelatedField(view_name='user_detail', lookup_field='username', read_only=True)
    editors = serializers.HyperlinkedRelatedField(many=True, view_name='user_detail', lookup_field='username', read_only=True)
    staff = serializers.HyperlinkedRelatedField(many=True, view_name='user_detail', lookup_field='username', read_only=True)

    def validate_url(self, value):
        if badgeanalysis.utils.test_probable_url(value):
            return value
        else:
            raise ValidationError("Issuer URL %s did not appear to be valid." % str(value))

    def create(self, validated_data, **kwargs):

        validated_data['badge_object'] = {
            '@context': utils.CURRENT_OBI_CONTEXT_IRI,
            'name': validated_data.get('name'),
            'url': validated_data.get('url'),
            'email': validated_data.get('email')
        }

        # remove keys that would confuse Issuer init from validated_data
        try:
            validated_data['badge_object']['description'] = validated_data.pop('description')
        except KeyError:
            pass

        new_issuer = Issuer(**validated_data)

        # Add @id to new issuer, which is depenent on an instance being initiated
        new_issuer.badge_object['@id'] = new_issuer.get_full_url()

        new_issuer.save()

        return new_issuer


class IssuerBadgeClassSerializer(AbstractBadgeObjectSerializer):
    issuer = serializers.HyperlinkedRelatedField(view_name='issuer_detail', read_only=True, lookup_field='slug')
    badge_object = WritableJSONField(max_length=16384, read_only=True, required=False)
    name = serializers.CharField(max_length=255)
    image = serializers.ImageField(allow_empty_file=False, use_url=True)
    slug = serializers.CharField(max_length=255, allow_blank=True, required=False)
    criteria_url = serializers.CharField(allow_blank=True, required=False)
    criteria_text = serializers.CharField(allow_blank=True, required=False)

    def validate_image(self, image):
        # TODO: Make sure it's a PNG (square if possible), and remove any baked-in badge assertion that exists.
        return image

    def validate_criteria_url(self, value):
        if badgeanalysis.utils.test_probable_url(value):
            return value
        else:
            raise serializers.ValidationError("Criteria URL " + value + " did not appear to be a valid URL.")

    def validate_criteria_text(self, value):
        if not isinstance(value, (str, unicode)):
            raise serializers.ValidationError("Provided criteria text could not be properly processed")
        else:
            return value

    def validate(self, data):
        # throw error for multiple competing criteria entries
        if data.get('criteria_url', u'') != u'' and data.get('criteria_text', u'') != u'':
            raise serializers.ValidationError(
                "Both criteria_text and criteria_url were provided. Use one or the other."
            )
        return data

    def create(self, validated_data, **kwargs):
        import pdb; pdb.set_trace();

        # TODO: except KeyError on pops for invalid keys? or just ensure they're there with validate()
        # "gets" data that must be in both model and model.badge_object, 
        # "pops" data that shouldn't be sent to model init
        validated_data['badge_object'] = {
            '@context': utils.CURRENT_OBI_CONTEXT_IRI,
            '@type': 'BadgeClass',
            'name': validated_data.get('name'),
            'description': validated_data.pop('description'),
            'criteria': validated_data.pop('criteria_url'),
            'issuer': validated_data.get('issuer').get_full_url()
        }

        # remove criteria_text from data before model init
        criteria_text = validated_data.pop('criteria_text')

        new_badgeclass = IssuerBadgeClass(**validated_data)

        full_url = new_badgeclass.get_full_url()
        # Augment with @id, image and criteria link
        new_badgeclass.badge_object['@id'] = full_url
        new_badgeclass.badge_object['image'] = full_url + '/image'

        current_criteria_url = new_badgeclass.badge_object.get('criteria')
        if current_criteria_url is None or current_criteria_url == '':
            new_badgeclass.badge_object['criteria'] = full_url + '/criteria'
            new_badgeclass.criteria_text = criteria_text

        new_badgeclass.save()
        return new_badgeclass


class IssuerAssertionSerializer(AbstractBadgeObjectSerializer):
    badge_object = WritableJSONField(max_length=16384, read_only=True, required=False)
    issuer = serializers.HyperlinkedRelatedField(view_name='issuer_detail', read_only=True)
    badgeclass = serializers.HyperlinkedRelatedField(view_name='badgeclass_detail', read_only=True)
    slug = serializers.CharField(max_length=255, read_only=True)
    image = serializers.ImageField(use_url=True, read_only=True)


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
