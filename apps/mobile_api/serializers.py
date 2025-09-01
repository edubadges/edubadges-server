from rest_framework import serializers
import json

from institution.models import Faculty, Institution
from issuer.models import BadgeInstance, BadgeClass, BadgeClassExtension, Issuer


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["name_dutch", "name_english", "image_dutch", "image_english"]


class FacultySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)

    class Meta:
        model = Faculty
        fields = ["name_dutch", "name_english", "image_dutch", "image_english", "on_behalf_of",
                  "on_behalf_of_display_name", "on_behalf_of_url", "institution"]


class IssuerSerializer(serializers.ModelSerializer):
    faculty = FacultySerializer(read_only=True)

    class Meta:
        model = Issuer
        fields = ["name_dutch", "name_english", "image_dutch", "image_english", "faculty"]


class BadgeClassExtensionSerializer(serializers.ModelSerializer):

    value = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClassExtension
        fields = ["name", "value"]

    def get_value(self, obj):
        json_dict = json.loads(obj.original_json)
        extension_key = json_dict["type"][1].split(":")[1].removesuffix("Extension")
        return json_dict[extension_key]


class BadgeClassSerializer(serializers.ModelSerializer):
    issuer = IssuerSerializer(read_only=True)

    class Meta:
        model = BadgeClass
        fields = ["id", "name", "entity_id", "image_url", "issuer"]


class BadgeClassDetailSerializer(serializers.ModelSerializer):
    issuer = IssuerSerializer(read_only=True)
    badgeclassextension_set = BadgeClassExtensionSerializer(many=True, read_only=True)

    class Meta:
        model = BadgeClass
        fields = ["id", "name", "entity_id", "image", "description", "formal", "participation", "assessment_type",
                  "assessment_id_verified", "assessment_supervised", "quality_assurance_name",
                  "badgeclassextension_set", "issuer"]


class BadgeInstanceSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassSerializer()

    class Meta:
        model = BadgeInstance
        fields = ["id", "created_at", "entity_id", "issued_on", "award_type", "revoked", "expires_at", "acceptance",
                  "public", "badgeclass"]


class BadgeInstanceDetailSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassDetailSerializer()

    class Meta:
        model = BadgeInstance
        fields = ["id", "created_at", "entity_id", "issued_on", "award_type", "revoked", "expires_at", "acceptance",
                  "public", "badgeclass"]
