from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from institution.models import Institution
from mainsite.exceptions import BadgrValidationError
from mainsite.serializers import StripTagsCharField, BadgrBaseModelSerializer, BaseSlugRelatedField
from .models import BadgeUser, CachedEmailAddress, TermsVersion, UserProvisionment


class UserSlugRelatedField(BaseSlugRelatedField):
    model = BadgeUser


class BadgeUserTokenSerializer(serializers.Serializer):
    class Meta:
        apispec_definition = ('BadgeUserToken', {})

    def to_representation(self, instance):
        representation = {
            'username': instance.username,
            'token': instance.cached_token()
        }
        if self.context.get('tokenReplaced', False):
            representation['replace'] = True
        return representation

    def update(self, instance, validated_data):
        # noop
        return instance


class InstitutionForProfileSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=512)

    class Meta:
        model = Institution


class BadgeUserProfileSerializer(serializers.Serializer):
    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', required=False)
    entity_id = serializers.CharField(read_only=True)
    agreed_terms_version = serializers.IntegerField(required=False)
    marketing_opt_in = serializers.BooleanField(required=False)
    institution = InstitutionForProfileSerializer(read_only=True, )

    class Meta:
        apispec_definition = ('BadgeUser', {})

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializer, self).to_representation(instance)
        latest = TermsVersion.cached.cached_latest()
        if latest:
            representation['latest_terms_version'] = latest.version
            if latest.version != instance.agreed_terms_version:
                representation['latest_terms_description'] = latest.short_description
        return representation


class EmailSerializer(BadgrBaseModelSerializer):
    variants = serializers.ListField(
        child=serializers.EmailField(required=False),
        required=False, source='cached_variants', allow_null=True, read_only=True
    )
    email = serializers.EmailField(required=True)

    class Meta:
        model = CachedEmailAddress
        fields = ('id', 'email', 'verified', 'primary', 'variants')
        read_only_fields = ('id', 'verified', 'primary', 'variants')
        apispec_definition = ('BadgeUserEmail', {

        })

    def create(self, validated_data):
        new_address = validated_data.get('email')
        created = False
        try:
            email = CachedEmailAddress.objects.get(email=new_address)
        except CachedEmailAddress.DoesNotExist:
            email = super(EmailSerializer, self).create(validated_data)
            created = True
        else:
            if not email.verified:
                email = super(EmailSerializer, self).create(validated_data)
                created = True
            elif email.user != self.context.get('request').user:
                raise serializers.ValidationError("Could not register email address.")

        if new_address != email.email and new_address not in [v.email for v in email.cached_variants()]:
            email.add_variant(new_address)
            raise serializers.ValidationError("Matching address already exists. New case variant registered.")

        if validated_data.get('variants'):
            for variant in validated_data.get('variants'):
                try:
                    email.add_variant(variant)
                except serializers.ValidationError:
                    pass
        if created:
            return email

        raise serializers.ValidationError("Could not register email address.")


class BadgeUserIdentifierField(serializers.CharField):
    def __init__(self, *args, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'created_by_id'
        if 'read_only' not in kwargs:
            kwargs['read_only'] = True
        super(BadgeUserIdentifierField, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return BadgeUser.cached.get(pk=value).primary_email
        except BadgeUser.DoesNotExist:
            return None


class UserProvisionmentSerializer(serializers.Serializer):
    user = UserSlugRelatedField(slug_field='entity_id', read_only=True)
    created_by = BadgeUserIdentifierField()
    email = serializers.EmailField(required=True)
    entity_id = serializers.CharField(read_only=True)
    content_type = serializers.PrimaryKeyRelatedField(queryset=ContentType.objects.all(), required=True)
    object_id = serializers.CharField(required=True)
    data = serializers.JSONField()
    for_teacher = serializers.BooleanField(required=True)
    type = serializers.CharField(required=True)
    notes = serializers.CharField(max_length=512, required=False)

    def validate(self, attrs):
        validated_data = super(UserProvisionmentSerializer, self).validate(attrs)
        entity = validated_data['content_type'].get_object_for_this_type(entity_id=validated_data['object_id'])
        if not entity.has_permissions(self.context['request'].user, ['may_administrate_users']):
            raise BadgrValidationError(fields='You do not have permission to invite user for this entity.')
        validated_data['object_id'] = entity.id
        return attrs

    def create(self, validated_data):
        prov = UserProvisionment(**validated_data)
        prov.find_and_match_user()
        prov.save()
        prov.send_email()
        return prov

    def to_representation(self, instance):
        return super(UserProvisionmentSerializer, self).to_representation(instance)


class UserProvisionmentSerializerForEdit(serializers.Serializer):

    data = serializers.JSONField()

    def update(self, instance, validated_data):
        if instance.rejected:
            raise BadgrValidationError(fields='You cannot edit an invitation that has been rejected.')
        if not instance.entity.has_permissions(self.context['request'].user, ['may_administrate_users']):
            raise BadgrValidationError(fields='You do not have permission to invite user for this entity.')
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance

