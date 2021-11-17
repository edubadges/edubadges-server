from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import PrimaryKeyRelatedField

from issuer.models import BadgeClass
from .models import LtiCourse


class LtiCourseSerializer(serializers.Serializer):
    identifier = serializers.CharField(max_length=255, required=True)
    title = serializers.CharField(max_length=255, required=False)
    label = serializers.CharField(max_length=255, required=True)
    badgeclass = PrimaryKeyRelatedField(many=False, queryset=BadgeClass.objects.all(), required=True)

    class Meta:
        model = LtiCourse

    def create(self, validated_data, **kwargs):
        user_permissions = validated_data['badgeclass'].get_permissions(validated_data['created_by'])
        if user_permissions['may_update']:
            new_lti_course = LtiCourse.objects.create(**validated_data)
            return new_lti_course
        else:
            raise ValidationError("You don't have the necessary permissions", 100)
