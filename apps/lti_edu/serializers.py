from rest_framework import serializers

from issuer.models import BadgeClass, Issuer
from lti_edu.models import StudentsEnrolled
from mainsite.serializers import BadgrBaseModelSerializer


class BadgeClassSerializer(BadgrBaseModelSerializer):
    """
    Used by LTI
    """

    class Meta:
        model = BadgeClass
        fields = '__all__'


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
