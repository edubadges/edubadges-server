from rest_framework import serializers
import json
from urllib.parse import urlencode

from badgeuser.models import BadgeUser, UserProvisionment, TermsAgreement, Terms, TermsUrl
from directaward.models import DirectAward
from institution.models import Faculty, Institution
from issuer.models import BadgeInstance, BadgeClass, BadgeClassExtension, Issuer, BadgeInstanceCollection
from lti_edu.models import StudentsEnrolled


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = ["name_dutch", "name_english", "image_dutch", "image_english",
                  "identifier", "alternative_identifier", "grondslag_formeel", "grondslag_informeel"]


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
        # Consistent naming convention enables to parse "type": ["Extension", "extensions:ECTSExtension"], "ECTS": 2.5}
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
    linkedin_url = serializers.SerializerMethodField()

    class Meta:
        model = BadgeInstance
        fields = ["id", "created_at", "entity_id", "issued_on", "award_type", "revoked", "expires_at", "acceptance",
                  "public", "badgeclass", "linkedin_url"]

    def _get_linkedin_org_id(self, badgeclass):
        issuer = badgeclass.issuer
        faculty = getattr(issuer, "faculty", None)
        if not faculty:
            return 206815

        if getattr(faculty, "linkedin_org_identifier", None):
            return faculty.linkedin_org_identifier

        institution = getattr(faculty, "institution", None)
        if getattr(institution, "linkedin_org_identifier", None):
            return institution.linkedin_org_identifier

        return 206815

    def get_linkedin_url(self, obj):
        request = self.context.get("request")
        if not request or not obj.issued_on:
            return None

        organization_id = self._get_linkedin_org_id(obj.badgeclass)

        cert_url = request.build_absolute_uri(
            f"/public/assertions/{obj.entity_id}"
        )

        params = {
            "startTask": "CERTIFICATION_NAME",
            "name": obj.badgeclass.name,
            "organizationId": organization_id,
            "issueYear": obj.issued_on.year,
            "issueMonth": obj.issued_on.month,
            "certUrl": cert_url,
            "certId": obj.entity_id,
            "original_referer": request.build_absolute_uri("/"),
        }

        return f"https://www.linkedin.com/profile/add?{urlencode(params)}"

class DirectAwardSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassSerializer()

    class Meta:
        model = DirectAward
        fields = ["id", "created_at", "entity_id", "badgeclass"]


class DirectAwardDetailSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassDetailSerializer()
    terms = serializers.SerializerMethodField()

    class Meta:
        model = DirectAward
        fields = ["id", "created_at", "status", "entity_id", "badgeclass", "terms"]

    def get_terms(self, obj):
        institution_terms = obj.badgeclass.issuer.faculty.institution.terms.all()
        serializer = TermsSerializer(institution_terms, many=True)
        return serializer.data


class StudentsEnrolledSerializer(serializers.ModelSerializer):
    badge_class = BadgeClassSerializer()

    class Meta:
        model = StudentsEnrolled
        fields = ["id", "entity_id", "date_created", "denied", "date_awarded", "badge_class"]


class StudentsEnrolledDetailSerializer(serializers.ModelSerializer):
    badge_class = BadgeClassDetailSerializer()

    class Meta:
        model = StudentsEnrolled
        fields = ["id", "entity_id", "date_created", "denied", "date_awarded", "badge_class"]


class BadgeCollectionSerializer(serializers.ModelSerializer):
    badge_instances = serializers.PrimaryKeyRelatedField(many=True, queryset=BadgeInstance.objects.all())

    class Meta:
        model = BadgeInstanceCollection
        fields = ["id", "created_at", "entity_id", "badge_instances", "name", "public", "description"]


class TermsUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsUrl
        fields = ["url", "language", "excerpt"]


class TermsSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    terms_urls = TermsUrlSerializer(many=True, read_only=True)

    class Meta:
        model = Terms
        fields = ["entity_id", "terms_type", "institution", "terms_urls"]


class TermsAgreementSerializer(serializers.ModelSerializer):
    terms = TermsSerializer(read_only=True)

    class Meta:
        model = TermsAgreement
        fields = ["entity_id", "agreed", "agreed_version", "terms"]


class UserSerializer(serializers.ModelSerializer):
    termsagreement_set = TermsAgreementSerializer(many=True, read_only=True)
    terms_agreed = serializers.SerializerMethodField()

    class Meta:
        model = BadgeUser
        fields = ["id", "email", "last_name", "first_name", "validated_name", "schac_homes", "terms_agreed",
                  "termsagreement_set"]

    def get_terms_agreed(self, obj):
        return obj.general_terms_accepted()
