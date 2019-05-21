from collections import OrderedDict
from datetime import datetime
from rest_framework import serializers
from issuer.models import BadgeClass, Issuer, BadgeInstance
from lti_edu.models import StudentsEnrolled, BadgeClassLtiContext
from cryptography.utils import read_only_property


class LTIrequestSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=150, default=1)
    lis_person_name_given = serializers.CharField(max_length=150)
    lis_person_name_family = serializers.CharField(max_length=150)
    lis_person_contact_email_primary = serializers.CharField(max_length=150)
    roles = serializers.ChoiceField(choices=['Instructor', 'Administrator', 'student'])

    tool_consumer_instance_name = serializers.CharField(max_length=150)
    custom_canvas_course_id = serializers.CharField(max_length=150)
    context_title = serializers.CharField(max_length=150)

class BadgeClassSerializer(serializers.ModelSerializer):
    """
    Used by LTI
    """
    class Meta:
        model = BadgeClass
        fields = '__all__'


class BadgeClassLtiContextSerializer(serializers.ModelSerializer):

    class Meta:
        model = BadgeClassLtiContext
        fields = ['badge_class','context_id']

    def to_representation(self, instance):
        data = {
            'badgeClassEntityId': instance.badge_class.entity_id,
            'contextId': instance.context_id,
            'name': instance.badge_class.name,
            'image':instance.badge_class.image.url,
        }
        return data




class StudentsEnrolledSerializer(serializers.ModelSerializer):
    """
    Used by LTI
    """
    class Meta:
        model = StudentsEnrolled
        fields = '__all__'
        

class IssuerSerializer(serializers.ModelSerializer):

    class Meta:
       model = Issuer
       fields = ('name',)


class BadgeClassSerializerWithRelations(serializers.ModelSerializer):
    issuer = IssuerSerializer()
    
    class Meta:
        model = BadgeClass
        fields = '__all__'


class StudentsEnrolledSerializerWithRelations(serializers.ModelSerializer):
    """
    Serializer of students enrolled with representation of it's relations to badgeclass and issuer
    """
    badge_class = BadgeClassSerializerWithRelations()
    revoked = serializers.SerializerMethodField('get_assertion_revokation')
    
    def get_assertion_revokation(self, enrollment):
        badge_instance = BadgeInstance.objects.filter(entity_id=enrollment.assertion_slug).first()
        if badge_instance:
            return badge_instance.revoked
        else:
            return False
    
    class Meta:
        model = StudentsEnrolled
        fields = '__all__'

    def to_representation(self, instance):
        ret = serializers.ModelSerializer.to_representation(self, instance)
        readable_date = str(datetime.strptime(ret['date_created'], '%Y-%m-%dT%H:%M:%S.%fZ').date())
        ret['date_created'] = readable_date
        return ret
