from rest_framework import serializers

from issuer.models import BadgeClass
from lti_edu.models import StudentsEnrolled


class LTIrequestSerializer(serializers.Serializer):
    user_id = serializers.CharField(max_length=150, default=1)
    lis_person_name_given = serializers.CharField(max_length=150)
    lis_person_name_family = serializers.CharField(max_length=150)
    lis_person_contact_email_primary = serializers.CharField(max_length=150)
    roles = serializers.ChoiceField(choices=['Instructor', 'Administrator', 'student'])

    tool_consumer_instance_name = serializers.CharField(max_length=150)
    custom_canvas_course_id = serializers.CharField(max_length=150)
    context_title = serializers.CharField(max_length=150)


class StudentsEnrolledSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentsEnrolled
        fields = '__all__'


class BadgeClassSerializer(serializers.ModelSerializer):
    class Meta:
        model = BadgeClass
        fields = '__all__'
