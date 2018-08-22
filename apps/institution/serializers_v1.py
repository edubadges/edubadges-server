from rest_framework import serializers
from rest_framework.serializers import UUIDField
from .models import Faculty, Institution



class InstitutionSerializerV1(serializers.Serializer):
    name = serializers.CharField(max_length=512)

    class Meta:
        model = Institution

class FacultySerializerV1(serializers.Serializer):
    id = serializers.ReadOnlyField()
    name = serializers.CharField(max_length=512)
#     institution = InstitutionSerializerV1()

    class Meta:
        model = Faculty