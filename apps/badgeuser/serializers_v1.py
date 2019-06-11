import json
from collections import OrderedDict
from django.conf import settings
from django.contrib.auth.models import Permission, Group
from rest_framework import serializers

from institution.serializers_v1 import FacultySerializerV1
from institution.models import Faculty
from mainsite.models import BadgrApp
from mainsite.serializers import StripTagsCharField
from mainsite.validators import PasswordValidator
from .models import BadgeUser, CachedEmailAddress, TermsVersion
from .utils import notify_on_password_change
from management.serializers import GroupSerializer

class BadgeUserTokenSerializerV1(serializers.Serializer):
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


class VerifiedEmailsField(serializers.Field):
    def to_representation(self, obj):
        addresses = []
        for emailaddress in obj.all():
            addresses.append(emailaddress.email)
        return addresses


class BadgeUserProfileSerializerV1(serializers.Serializer):
    first_name = StripTagsCharField(max_length=30, allow_blank=True)
    last_name = StripTagsCharField(max_length=30, allow_blank=True)
    email = serializers.EmailField(source='primary_email', required=False)
    current_password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False)
    password = serializers.CharField(style={'input_type': 'password'}, write_only=True, required=False, validators=[PasswordValidator()])
    slug = serializers.CharField(source='entity_id', read_only=True)
    agreed_terms_version = serializers.IntegerField(required=False)
    marketing_opt_in = serializers.BooleanField(required=False)
    user_permissions = serializers.SerializerMethodField(required=False)
    faculty = FacultySerializerV1(many=True,  allow_null=True)

    class Meta:
        apispec_definition = ('BadgeUser', {})

    def get_user_permissions(self, obj):
        perms = obj.user_permissions.all() | Permission.objects.filter(group__user=obj)
        perms = list(x.codename for x in perms)
        if obj.is_staff:
            perms.insert(0, u'is_staff')
        if obj.is_superuser:
            perms.insert(0,u'is_superuser')
        return json.dumps(perms)

    def create(self, validated_data):
        user = BadgeUser.objects.create(
            email=validated_data['primary_email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            plaintext_password=validated_data['password'],
            marketing_opt_in=validated_data.get('marketing_opt_in', False),
            request=self.context.get('request', None),
        )
        return user

    def update(self, user, validated_data):
        first_name = validated_data.get('first_name')
        last_name = validated_data.get('last_name')
        password = validated_data.get('password')
        current_password = validated_data.get('current_password')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name

        if password:
            if not current_password:
                raise serializers.ValidationError({'currrent_password': "Field is required"})
            if user.check_password(current_password):
                user.set_password(password)
                notify_on_password_change(user)
            else:
                raise serializers.ValidationError({'currrent_password': "Incorrect password"})

        if 'agreed_terms_version' in validated_data:
            user.agreed_terms_version = validated_data.get('agreed_terms_version')

        if 'marketing_opt_in' in validated_data:
            user.marketing_opt_in = validated_data.get('marketing_opt_in')

        user.save()
        return user

    def to_representation(self, instance):
        representation = super(BadgeUserProfileSerializerV1, self).to_representation(instance)

        latest = TermsVersion.cached.cached_latest()
        if latest:
            representation['latest_terms_version'] = latest.version
            if latest.version != instance.agreed_terms_version:
                representation['latest_terms_description'] = latest.short_description

        return representation


class EmailSerializerV1(serializers.ModelSerializer):
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
            email = super(EmailSerializerV1, self).create(validated_data)
            created = True
        else:
            if not email.verified:
                # Clear out a previous attempt and let the current user try
                email.delete()
                email = super(EmailSerializerV1, self).create(validated_data)
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


class BadgeUserIdentifierFieldV1(serializers.CharField):
    def __init__(self, *args, **kwargs):
        if 'source' not in kwargs:
            kwargs['source'] = 'created_by_id'
        if 'read_only' not in kwargs:
            kwargs['read_only'] = True
        super(BadgeUserIdentifierFieldV1, self).__init__(*args, **kwargs)

    def to_representation(self, value):
        try:
            return BadgeUser.cached.get(pk=value).primary_email
        except BadgeUser.DoesNotExist:
            return None


class BadgeUserManagementSerializer(serializers.ModelSerializer):

    first_name = serializers.CharField(read_only=True, max_length=512)
    last_name = serializers.CharField(read_only=True, max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')
    faculties = FacultySerializerV1(many=True,  allow_null=True, source='faculty')
    email = serializers.EmailField(source='primary_email', read_only=True)
    groups = GroupSerializer(many=True, allow_null=True)

    class Meta:
        model = BadgeUser
        fields = ('first_name', 'last_name', 'slug', 'faculties', 'email', 'groups')

    def filter_groups_by_user_scope(self, groups):
        highest_user_rank = self.context['request'].user.highest_group.rank
        groups_within_scope = []
        for group in groups:
            if group.rank >= highest_user_rank:
                groups_within_scope.append(group)
        return groups_within_scope

    def filter_faculties_by_user_scope(self, faculties):
        faculties_within_scope = []
        for faculty in faculties:
            if self.context['request'].user.within_scope(faculty):
                faculties_within_scope.append(faculty)
        return faculties_within_scope

    def to_representation(self, instance):
        representation = super(BadgeUserManagementSerializer, self).to_representation(instance)
        faculties = [Faculty.objects.get(entity_id=faculty['slug']) for faculty in representation['faculties']]
        groups = [Group.objects.get(entity_id=group['slug']) for group in representation['groups']]
        representation['faculties'] = [FacultySerializerV1().to_representation(faculty) for faculty in self.filter_faculties_by_user_scope(faculties)]
        representation['groups'] = [GroupSerializer().to_representation(group) for group in self.filter_groups_by_user_scope(groups)]
        return representation

    def to_internal_value(self, data):
        internal_value = super(BadgeUserManagementSerializer, self).to_internal_value(data)
        internal_value['faculty'] = [OrderedDict(fac) for fac in data['faculties']]
        internal_value['groups'] = [OrderedDict(group) for group in data['groups']]
        return internal_value

    def update(self, instance, validated_data):
        current_faculties = set(self.filter_faculties_by_user_scope([i for i in instance.faculty.all()]))
        current_groups = set(self.filter_groups_by_user_scope([i for i in instance.groups.all()]))
        new_faculties = set([Faculty.objects.get(entity_id=d['slug']) for d in validated_data['faculty']])
        new_groups = set([Group.objects.get(entity_id=d['slug']) for d in validated_data['groups']])

        faculties_to_remove = current_faculties.difference(new_faculties)
        faculties_to_add = new_faculties.difference(current_faculties)
        groups_to_remove = current_groups.difference(new_groups)
        groups_to_add = new_groups.difference(current_groups)

        if faculties_to_remove or faculties_to_add:
            for faculty in faculties_to_remove.union(faculties_to_add):
                if not self.context['request'].user.within_scope(faculty):
                    raise serializers.ValidationError("Faculty outside scope.")

        if groups_to_remove or groups_to_add:
            for group in groups_to_remove.union(groups_to_add):
                if group.rank < self.context['request'].user.highest_group.rank:
                    raise serializers.ValidationError("Group outside scope.")

        if faculties_to_remove:
            for fac in faculties_to_remove:
                instance.faculty.remove(fac)
                pass
        if faculties_to_add:
            for fac in faculties_to_add:
                instance.faculty.add(fac)
        if groups_to_remove:
            for group in groups_to_remove:
                instance.groups.remove(group)
                pass
        if groups_to_add:
            for group in groups_to_add:
                instance.groups.add(group)

        instance.save()
        return instance
