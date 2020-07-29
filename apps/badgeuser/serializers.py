from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from institution.models import Institution
from mainsite.exceptions import BadgrValidationError
from mainsite.serializers import StripTagsCharField, BadgrBaseModelSerializer, BaseSlugRelatedField
from .models import BadgeUser, CachedEmailAddress, UserProvisionment, Terms


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
    marketing_opt_in = serializers.BooleanField(required=False)
    institution = InstitutionForProfileSerializer(read_only=True, )

    class Meta:
        apispec_definition = ('BadgeUser', {})


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
            raise BadgrValidationError('You do not have permission to invite user for this entity.', 507)
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
            raise BadgrValidationError('You cannot edit an invitation that has been rejected.', 508)
        if not instance.entity.has_permissions(self.context['request'].user, ['may_administrate_users']):
            raise BadgrValidationError('You do not have permission to invite user for this entity.', 507)
        [setattr(instance, attr, validated_data.get(attr)) for attr in validated_data]
        instance.save()
        return instance


class TermsSerializer(serializers.Serializer):
    entity_id = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    language = serializers.CharField(read_only=True)
    terms_type = serializers.CharField(read_only=True)
    version = serializers.IntegerField(read_only=True)

    class Meta:
        model = Terms


class TermsAgreementSerializer(serializers.Serializer):
    agreed = serializers.CharField(required=False)
    agreed_version = serializers.BooleanField(required=False)
    terms = TermsSerializer(required=False)
    terms_entity_id = serializers.CharField(required=False)
    accepted = serializers.BooleanField(required=False)

    def create(self, validated_data):
        terms = Terms.objects.get(entity_id=validated_data['terms_entity_id'])
        if terms.institution:
            if not terms.institution.identifier in self.context['request'].user.get_all_associated_institutions_identifiers():
                raise BadgrValidationError('You cannot accept terms that are not from your institution', 0)
        if validated_data['accepted']:
            return terms.accept(self.context['request'].user)

    def to_representation(self, instance):
        return super(TermsAgreementSerializer, self).to_representation(instance)
