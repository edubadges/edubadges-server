from datetime import datetime
from rest_framework import serializers
from issuer.models import BadgeClass, Issuer, BadgeInstance
from lti_edu.models import StudentsEnrolled, LtiClient, get_uuid
from mainsite.serializers import StripTagsCharField #, RelationPrimaryKeyAsSlugCharField



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


class LtiClientsSerializer(serializers.ModelSerializer):

    name = serializers.CharField(max_length=512)
    slug = StripTagsCharField(max_length=255, read_only=True, source='entity_id')

    class Meta:
        model = LtiClient
        fields = ('name', 'slug')

    def to_internal_value(self, data):
        internal_value = super(LtiClientsSerializer, self).to_internal_value(data)
        issuer_slug = data.get("issuer_slug")
        issuer = Issuer.objects.get(entity_id=issuer_slug)
        internal_value.update({
            "issuer": issuer
        })
        return internal_value

    def update(self, instance, validated_data):
        issuer_slug = validated_data.pop('issuer_slug')
        instance.issuer = Issuer.objects.get(entity_id=issuer_slug)
        instance.name = validated_data.get('name')
        instance.save()
        return instance

    def create(self, validated_data, **kwargs):
        del validated_data['created_by']
        validated_data['shared_secret'] = get_uuid()
        validated_data['consumer_key'] = get_uuid()
        new_client = LtiClient(**validated_data)
        new_client.save()
        return new_client