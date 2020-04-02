from rest_framework import serializers
from rest_framework.serializers import SlugRelatedField
from badgeuser.models import BadgeUser
from institution.models import Institution, Faculty
from issuer.models import Issuer, BadgeClass
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class BaseSlugRelatedField(SlugRelatedField):
    def get_queryset(self):
        return self.model.objects.all()


class UserSlugRelatedField(BaseSlugRelatedField):
    model = BadgeUser


class InstitutionSlugRelatedField(BaseSlugRelatedField):
    model = Institution


class FacultySlugRelatedField(BaseSlugRelatedField):
    model = Faculty


class IssuerSlugRelatedField(BaseSlugRelatedField):
    model = Issuer


class BadgeClassSlugRelatedField(BaseSlugRelatedField):
    model = BadgeClass


class BaseStaffSerializer(serializers.Serializer):
    user = UserSlugRelatedField(slug_field='entity_id', required=True)
    may_create = serializers.CharField(allow_blank=False, required=True)
    may_read = serializers.CharField(allow_blank=False, required=True)
    may_update = serializers.CharField(allow_blank=False, required=True)
    may_delete = serializers.CharField(allow_blank=False, required=True)
    may_sign = serializers.CharField(allow_blank=False, required=True)
    may_award = serializers.CharField(allow_blank=False, required=True)
    may_administrate_users = serializers.CharField(allow_blank=False, required=True)

    def _base_create(self, validated_data, object_name, object_class):
        created_by = validated_data.pop('created_by')
        if created_by.is_user_within_scope(validated_data['user']):
            perms_allowed_to_assign = validated_data[object_name].get_permissions(created_by)
            for perm in perms_allowed_to_assign:
                if not perms_allowed_to_assign[perm] and int(validated_data[perm]):
                    raise serializers.ValidationError("May not assign permissions that you don't have yourself")
            return object_class.objects.create(**validated_data)
        else:
            raise serializers.ValidationError("You may not administrate this user.")

    def update(self, instance, validated_data):
        if instance.user.entity_id != validated_data['user'].entity_id:
            raise serializers.ValidationError("Changing users of staff memberships is not allowed")
        created_by = validated_data.pop('updated_by')
        perms_allowed_to_change = validated_data[instance.object.__class__.__name__.lower()].get_permissions(created_by)
        original_perms = instance.permissions
        for permission in original_perms.keys():
            new_value = bool(int(validated_data[permission]))
            original_value = original_perms[permission]
            if original_value != new_value:  # this permission is changed
                if not perms_allowed_to_change[permission]:
                    raise serializers.ValidationError("May not change permissions that you don't have yourself")
                else:
                    setattr(instance, permission, new_value)  # update the permission
        instance.save()
        return instance


class InstitutionStaffSerializer(BaseStaffSerializer):
    institution = InstitutionSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        return self._base_create(validated_data, 'institution', InstitutionStaff)


class FacultyStaffSerializer(BaseStaffSerializer):
    faculty = FacultySlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        return self._base_create(validated_data, 'faculty', FacultyStaff)


class IssuerStaffSerializer(BaseStaffSerializer):
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        return self._base_create(validated_data, 'issuer', IssuerStaff)


class BadgeClassStaffSerializer(BaseStaffSerializer):
    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        return self._base_create(validated_data, 'badgeclass', BadgeClassStaff)

