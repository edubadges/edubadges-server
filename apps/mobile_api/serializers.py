import json
from urllib.parse import urlencode

from badgeuser.models import BadgeUser, Terms, TermsAgreement, TermsUrl
from directaward.models import DirectAward
from institution.models import Faculty, Institution
from issuer.models import BadgeClass, BadgeClassExtension, BadgeInstance, BadgeInstanceCollection, Issuer
from lti_edu.models import StudentsEnrolled
from rest_framework import serializers


class InstitutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Institution
        fields = [
            'name_dutch',
            'name_english',
            'image_dutch',
            'image_english',
            'identifier',
            'alternative_identifier',
            'grondslag_formeel',
            'grondslag_informeel',
        ]


class FacultySerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)

    class Meta:
        model = Faculty
        fields = [
            'name_dutch',
            'name_english',
            'image_dutch',
            'image_english',
            'on_behalf_of',
            'on_behalf_of_display_name',
            'on_behalf_of_url',
            'institution',
        ]


class IssuerSerializer(serializers.ModelSerializer):
    faculty = FacultySerializer(read_only=True)

    class Meta:
        model = Issuer
        fields = ['name_dutch', 'name_english', 'image_dutch', 'image_english', 'faculty']


class BadgeClassExtensionSerializer(serializers.ModelSerializer):
    value = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClassExtension
        fields = ['name', 'value']

    def get_value(self, obj):
        json_dict = json.loads(obj.original_json)
        # Consistent naming convention enables to parse "type": ["Extension", "extensions:ECTSExtension"], "ECTS": 2.5}
        extension_key = json_dict['type'][1].split(':')[1].removesuffix('Extension')
        return json_dict[extension_key]


class BadgeClassSerializer(serializers.ModelSerializer):
    issuer = IssuerSerializer(read_only=True)

    class Meta:
        model = BadgeClass
        fields = ['id', 'name', 'entity_id', 'image_url', 'issuer']


class BadgeClassDetailSerializer(serializers.ModelSerializer):
    issuer = IssuerSerializer(read_only=True)
    badgeclassextension_set = BadgeClassExtensionSerializer(many=True, read_only=True)

    class Meta:
        model = BadgeClass
        fields = [
            'id',
            'name',
            'entity_id',
            'image',
            'description',
            'formal',
            'participation',
            'assessment_type',
            'assessment_id_verified',
            'assessment_supervised',
            'quality_assurance_name',
            'stackable',
            'badgeclassextension_set',
            'issuer',
            'badge_class_type', 
            'expiration_period',
        ]


class BadgeInstanceSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassSerializer()

    class Meta:
        model = BadgeInstance
        fields = [
            'id',
            'created_at',
            'entity_id',
            'issued_on',
            'award_type',
            'revoked',
            'expires_at',
            'acceptance',
            'public',
            'badgeclass',
            'grade_achieved',
            "include_grade_achieved"
        ]


class BadgeInstanceDetailSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassDetailSerializer()
    linkedin_url = serializers.SerializerMethodField()

    class Meta:
        model = BadgeInstance
        fields = [
            'id',
            'created_at',
            'entity_id',
            'issued_on',
            'award_type',
            'revoked',
            'expires_at',
            'acceptance',
            'public',
            'badgeclass',
            'linkedin_url',
            'grade_achieved',
            'include_grade_achieved',
            'include_evidence'
        ]

    def _get_linkedin_org_id(self, badgeclass):
        faculty = badgeclass.issuer.faculty

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
        fields = ['id', 'created_at', 'entity_id', 'badgeclass']


class DirectAwardDetailSerializer(serializers.ModelSerializer):
    badgeclass = BadgeClassDetailSerializer()
    terms = serializers.SerializerMethodField()

    class Meta:
        model = DirectAward
        fields = ['id', 'created_at', 'status', 'entity_id', 'badgeclass', 'terms']

    def get_terms(self, obj):
        institution_terms = obj.badgeclass.issuer.faculty.institution.terms.all()
        serializer = TermsSerializer(institution_terms, many=True)
        return serializer.data


class StudentsEnrolledSerializer(serializers.ModelSerializer):
    badge_class = BadgeClassSerializer()

    class Meta:
        model = StudentsEnrolled
        fields = ['id', 'entity_id', 'date_created', 'denied', 'date_awarded', 'badge_class']


class StudentsEnrolledDetailSerializer(serializers.ModelSerializer):
    badge_class = BadgeClassDetailSerializer()

    class Meta:
        model = StudentsEnrolled
        fields = ['id', 'entity_id', 'date_created', 'denied', 'date_awarded', 'badge_class']


class BadgeCollectionSerializer(serializers.ModelSerializer):
    badge_instances = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='entity_id'
    )

    class Meta:
        model = BadgeInstanceCollection
        fields = ['id', 'created_at', 'entity_id', 'badge_instances', 'name', 'public', 'description']


class TermsUrlSerializer(serializers.ModelSerializer):
    class Meta:
        model = TermsUrl
        fields = ['url', 'language', 'excerpt']


class TermsSerializer(serializers.ModelSerializer):
    institution = InstitutionSerializer(read_only=True)
    terms_urls = TermsUrlSerializer(many=True, read_only=True)

    class Meta:
        model = Terms
        fields = ['entity_id', 'terms_type', 'institution', 'terms_urls']


class TermsAgreementSerializer(serializers.ModelSerializer):
    terms = TermsSerializer(read_only=True)

    class Meta:
        model = TermsAgreement
        fields = ['entity_id', 'agreed', 'agreed_version', 'terms']


class UserSerializer(serializers.ModelSerializer):
    termsagreement_set = TermsAgreementSerializer(many=True, read_only=True)
    terms_agreed = serializers.BooleanField(read_only=True)

    class Meta:
        model = BadgeUser
        fields = [
            'id',
            'email',
            'last_name',
            'first_name',
            'validated_name',
            'schac_homes',
            'terms_agreed',
            'termsagreement_set',
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    institution = serializers.SlugRelatedField(slug_field='name', read_only=True)
    termsagreement_set = TermsAgreementSerializer(many=True, read_only=True)
    terms_agreed = serializers.BooleanField(read_only=True)

    class Meta:
        model = BadgeUser
        fields = [
            'entity_id',
            'first_name',
            'last_name',
            'email',
            'institution',
            'marketing_opt_in',
            'is_superuser',
            'validated_name',
            'schac_homes',
            'terms_agreed',
            'termsagreement_set',
        ]


class CatalogBadgeClassSerializer(serializers.ModelSerializer):
    # BadgeClass fields
    created_at = serializers.DateTimeField(read_only=True)
    name = serializers.CharField()
    image = serializers.ImageField()
    archived = serializers.BooleanField()
    entity_id = serializers.CharField(read_only=True)
    is_private = serializers.BooleanField()
    is_micro_credentials = serializers.BooleanField()
    badge_class_type = serializers.CharField()
    required_terms = serializers.SerializerMethodField()
    user_has_accepted_terms = serializers.SerializerMethodField()

    # Issuer fields
    issuer_name_english = serializers.CharField(source='issuer.name_english', read_only=True)
    issuer_name_dutch = serializers.CharField(source='issuer.name_dutch', read_only=True)
    issuer_entity_id = serializers.CharField(source='issuer.entity_id', read_only=True)
    issuer_image_dutch = serializers.CharField(source='issuer.image_dutch', read_only=True)
    issuer_image_english = serializers.CharField(source='issuer.image_english', read_only=True)

    # Faculty fields
    faculty_name_english = serializers.CharField(source='issuer.faculty.name_english', read_only=True)
    faculty_name_dutch = serializers.CharField(source='issuer.faculty.name_dutch', read_only=True)
    faculty_entity_id = serializers.CharField(source='issuer.faculty.entity_id', read_only=True)
    faculty_image_dutch = serializers.CharField(source='issuer.faculty.image_dutch', read_only=True)
    faculty_image_english = serializers.CharField(source='issuer.faculty.image_english', read_only=True)
    faculty_on_behalf_of = serializers.BooleanField(source='issuer.faculty.on_behalf_of', read_only=True)
    faculty_type = serializers.CharField(source='issuer.faculty.faculty_type', read_only=True)

    # Institution fields
    institution_name_english = serializers.CharField(source='issuer.faculty.institution.name_english', read_only=True)
    institution_name_dutch = serializers.CharField(source='issuer.faculty.institution.name_dutch', read_only=True)
    institution_entity_id = serializers.CharField(source='issuer.faculty.institution.entity_id', read_only=True)
    institution_image_dutch = serializers.CharField(source='issuer.faculty.institution.image_dutch', read_only=True)
    institution_image_english = serializers.CharField(source='issuer.faculty.institution.image_english', read_only=True)
    institution_type = serializers.CharField(source='issuer.faculty.institution.institution_type', read_only=True)

    # Annotated counts
    self_requested_assertions_count = serializers.IntegerField(read_only=True)
    direct_awarded_assertions_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = BadgeClass
        fields = [
            # BadgeClass
            'created_at',
            'name',
            'image',
            'archived',
            'entity_id',
            'is_private',
            'is_micro_credentials',
            'badge_class_type',
            'required_terms',
            'user_has_accepted_terms',

            # Issuer
            'issuer_name_english',
            'issuer_name_dutch',
            'issuer_entity_id',
            'issuer_image_dutch',
            'issuer_image_english',

            # Faculty
            'faculty_name_english',
            'faculty_name_dutch',
            'faculty_entity_id',
            'faculty_image_dutch',
            'faculty_image_english',
            'faculty_on_behalf_of',
            'faculty_type',

            # Institution
            'institution_name_english',
            'institution_name_dutch',
            'institution_entity_id',
            'institution_image_dutch',
            'institution_image_english',
            'institution_type',

            # Counts
            'self_requested_assertions_count',
            'direct_awarded_assertions_count'
        ]

    def get_required_terms(self, obj):
        try:
            terms = obj.get_required_terms()
        except ValueError:
            return None  # Should not break the serializer

        return TermsSerializer(terms, context=self.context).data

    def get_user_has_accepted_terms(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        user = request.user
        return obj.terms_accepted(user)
