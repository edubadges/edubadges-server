from graphene.types.json import JSONString
from graphene_django.types import DjangoObjectType
from django.contrib.contenttypes.models import ContentType


class JSONType(JSONString):
    @staticmethod
    def serialize(dt):
        return dt


class ContentTypeType(DjangoObjectType):
    class Meta:
        model = ContentType
        fields = ('id',)
