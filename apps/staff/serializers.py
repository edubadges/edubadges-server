from rest_framework import serializers
from institution.serializers_v1 import InstitutionSerializerV1, FacultySerializerV1
from issuer.serializers_v1 import IssuerSerializerV1, BadgeClassSerializerV1


class InstitutionStaffSerializer:

    institution = InstitutionSerializerV1(read_only=True)


class FacultyStaffSerializer:

    faculty = FacultySerializerV1(read_only=True)


class IssuerStaffSerializer:

    issuer = IssuerSerializerV1(read_only=True)


class BadgeClassStaffSerializer:

    badgeclass = BadgeClassSerializerV1(read_only=True)


class StaffSerializer(serializers.Serializer):
    create = serializers.CharField(allow_blank=False, required=True)
    read = serializers.CharField(allow_blank=False, required=True)
    update = serializers.CharField(allow_blank=False, required=True)
    destroy = serializers.CharField(allow_blank=False, required=True)
    administrate_users = serializers.CharField(allow_blank=False, required=True)
    object = serializers.SerializerMethodField()

    def get_object(self, obj):
        serializer = obj.serializer_class(obj)
        return serializer.to_representation()
