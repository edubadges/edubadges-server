from issuer.models import BadgeClass, Issuer, IssuerStaff
from lti_edu.models import StudentsEnrolled, BadgeClassLtiContext
from mainsite.drf_fields import ValidImageField
from mainsite.serializers import StripTagsCharField, BadgrBaseModelSerializer
from rest_framework import serializers


class BadgeClassSerializer(BadgrBaseModelSerializer):
    """
    Used by LTI
    """
    class Meta:
        model = BadgeClass
        fields = '__all__'


class BadgeClassLtiContextSerializer(BadgrBaseModelSerializer):
    badgeClassEntityId = serializers.CharField(source='badge_class.entity_id')
    contextId = serializers.CharField(source='context_id')
    name = serializers.CharField(source='badge_class.name')
    image = ValidImageField(source='badge_class.image')
    issuer_slug = serializers.CharField(source='badge_class.issuer.entity_id')
    can_award = serializers.SerializerMethodField()

    class Meta:
        model = BadgeClassLtiContext
        fields = ['badgeClassEntityId','contextId','name','image','issuer_slug','can_award']

    def get_can_award(self,obj):
        user = self.context['request'].user
        if user in obj.badge_class.issuer.staff.all():
            if IssuerStaff.objects.filter(user=user,issuer=obj.badge_class.issuer).all()[0].role in \
                    [IssuerStaff.ROLE_OWNER ,IssuerStaff.ROLE_EDITOR,IssuerStaff.ROLE_STAFF]:
                return True
        return False


class BadgeClassLtiContextStudentSerializer(BadgrBaseModelSerializer):
    badgeClassEntityId = serializers.CharField(source='badge_class.entity_id')
    contextId = serializers.CharField(source='context_id')
    name = serializers.CharField(source='badge_class.name')
    image = ValidImageField(source='badge_class.image')
    requested = serializers.SerializerMethodField()
    rewarded = serializers.SerializerMethodField()
    denied = serializers.SerializerMethodField()
    revoked = serializers.SerializerMethodField()


    class Meta:
        model = BadgeClassLtiContext
        fields = ['badgeClassEntityId','contextId','name','image','requested','rewarded','denied','revoked']

    def get_requested(self, obj):
        user = self.context['request'].user
        if user.is_student() and not self.get_revoked(obj):
            if StudentsEnrolled.objects.filter(user=user, badge_class=obj.badge_class, date_awarded__isnull=True, denied=False).exists():
                return True
        return False

    def get_rewarded(self,obj):
        user = self.context['request'].user
        if user.is_student():
            if StudentsEnrolled.objects.filter(user=user, badge_class=obj.badge_class,
                                               date_awarded__isnull=False, denied=False).exists() \
                    and not self.get_revoked(obj):
                return True
        return False

    def get_denied(self,obj):
        user = self.context['request'].user
        if user.is_student():
            if StudentsEnrolled.objects.filter(user=user, badge_class=obj.badge_class, denied=True).exists():
                return True
        return False

    def get_revoked(self,obj):
        user = self.context['request'].user
        if user.is_student():

            assertions = StudentsEnrolled.objects.filter(user=user, badge_class=obj.badge_class).all()
            if len(assertions) > 0:
                assertion = assertions[0]
            else:
                return False
            if assertion.assertion_is_revoked():
                return True
        return False


class IssuerSerializer(BadgrBaseModelSerializer):

    class Meta:
       model = Issuer
       fields = ('name',)


class BadgeClassSerializerWithRelations(BadgrBaseModelSerializer):
    issuer = IssuerSerializer()
    
    class Meta:
        model = BadgeClass
        fields = '__all__'


class StudentsEnrolledSerializerWithRelations(BadgrBaseModelSerializer):
    """
    Serializer of students enrolled with representation of it's relations to badgeclass and issuer
    """
    badge_class = BadgeClassSerializerWithRelations()
    revoked = serializers.SerializerMethodField('get_assertion_revokation')
    
    def get_assertion_revokation(self, enrollment):
        badge_instance = enrollment.badge_instance
        if badge_instance:
            return badge_instance.revoked
        else:
            return False
    
    class Meta:
        model = StudentsEnrolled
        fields = '__all__'

    def to_representation(self, instance):
        ret = serializers.ModelSerializer.to_representation(self, instance)
        day_as_string = ret['date_created'].split('T')[0]
        ret['date_created'] = day_as_string
        return ret

