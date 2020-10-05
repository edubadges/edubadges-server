from rest_framework import serializers
from badgeuser.serializers import UserSlugRelatedField
from institution.serializers import InstitutionSlugRelatedField, FacultySlugRelatedField
from issuer.serializers import IssuerSlugRelatedField, BadgeClassSlugRelatedField
from mainsite.utils import EmailMessageMaker
from staff.models import InstitutionStaff, FacultyStaff, IssuerStaff, BadgeClassStaff


class BaseStaffSerializer(serializers.Serializer):

    may_create = serializers.CharField(allow_blank=False, required=True)
    may_read = serializers.CharField(allow_blank=False, required=True)
    may_update = serializers.CharField(allow_blank=False, required=True)
    may_delete = serializers.CharField(allow_blank=False, required=True)
    may_sign = serializers.CharField(allow_blank=False, required=True)
    may_award = serializers.CharField(allow_blank=False, required=True)
    may_administrate_users = serializers.CharField(allow_blank=False, required=True)


class StaffUpdateSerializer(BaseStaffSerializer):

    def update(self, instance, validated_data):
        original_perms = instance.permissions
        for permission in original_perms.keys():
            new_value = bool(int(validated_data[permission]))
            original_value = original_perms[permission]
            if original_value != new_value:  # this permission is changed
                setattr(instance, permission, new_value)  # update the permission
        instance.save()
        html_message = EmailMessageMaker.create_staff_rights_changed_email(instance)
        subject = 'You role has changed for you staff membership for the {entity_type} {entity_name}'.format(
            entity_type=instance.object.__class__.__name__.lower(),
            entity_name=instance.object.name
            )
        instance.user.email_user(subject=subject, html_message=html_message)
        return instance


class BaseStaffCreateSerializer(BaseStaffSerializer):
    user = UserSlugRelatedField(slug_field='entity_id', required=True)

    def _base_create(self, validated_data, object_name, object_class):
        created_by = validated_data.pop('created_by')
        if created_by.is_user_within_scope(validated_data['user']):
            perms_allowed_to_assign = validated_data[object_name].get_permissions(created_by)
            for perm in perms_allowed_to_assign:
                if not perms_allowed_to_assign[perm] and int(validated_data[perm]):
                    raise serializers.ValidationError("May not assign permissions that you don't have yourself")
            new_staff_membership = object_class.objects.create(**validated_data)
            message = EmailMessageMaker.create_staff_member_addition_email(new_staff_membership)
            entity_name = new_staff_membership.object.__class__.__name__
            determiner = 'an' if entity_name[0] in 'aeiouAEIOU' else 'a'
            new_staff_membership.user.email_user(subject='You have been added to {} {}'.format(determiner, entity_name),
                                                 html_message=message)
            return new_staff_membership
        else:
            raise serializers.ValidationError("You may not administrate this user.")


class InstitutionStaffSerializer(BaseStaffCreateSerializer):
    institution = InstitutionSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        institution_staff_membership = self._base_create(validated_data, 'institution', InstitutionStaff)
        # Clean up lower permissions - we only support institution admin's so we don't need to check any permissions
        user = validated_data['user']
        # Trigger cache deletion
        [staff.delete() for staff in user.badgeclassstaff_set.all()]
        [staff.delete() for staff in user.issuerstaff_set.all()]
        [staff.delete() for staff in user.facultystaff_set.all()]
        return institution_staff_membership


class FacultyStaffSerializer(BaseStaffCreateSerializer):
    faculty = FacultySlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        faculty_staff_membership = self._base_create(validated_data, 'faculty', FacultyStaff)
        fac = faculty_staff_membership.faculty
        # Clean up lower permissions for this faculty - we only support faculty admin's so we can delete all
        user = validated_data['user']
        # Trigger cache deletion
        [staff.delete() for staff in user.badgeclassstaff_set.all() if staff.badgeclass.issuer.faculty == fac]
        [staff.delete() for staff in user.issuerstaff_set.all() if staff.issuer.faculty == fac]
        return faculty_staff_membership


class IssuerStaffSerializer(BaseStaffCreateSerializer):
    issuer = IssuerSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        issuer_staff_membership = self._base_create(validated_data, 'issuer', IssuerStaff)
        iss = issuer_staff_membership.issuer
        # Clean up lower permissions for this issuer - we only support issuer admin's so we can delete all
        user = validated_data['user']
        # Trigger cache deletion
        [staff.delete() for staff in user.badgeclassstaff_set.all() if staff.badgeclass.issuer == iss]
        return issuer_staff_membership


class BadgeClassStaffSerializer(BaseStaffCreateSerializer):
    badgeclass = BadgeClassSlugRelatedField(slug_field='entity_id', required=True)

    def create(self, validated_data):
        return self._base_create(validated_data, 'badgeclass', BadgeClassStaff)

