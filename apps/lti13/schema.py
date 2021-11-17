import graphene
from graphene_django.types import DjangoObjectType

from .models import LtiCourse, LtiTool


class LtiToolType(DjangoObjectType):
    class Meta:
        model = LtiTool
        fields = ('id', 'title', 'description', 'issuer')


class LtiCourseType(DjangoObjectType):
    class Meta:
        model = LtiCourse
        fields = ('entity_id', 'created_at', 'identifier', 'title', 'tool')

    tool = graphene.Field(LtiToolType)

    def resolve_tool(self, info, **kwargs):
        return self.tool


class Query(object):
    lti_course = graphene.Field(LtiCourseType, badge_class_id=graphene.String())
    lti_tool = graphene.Field(LtiToolType, client_id=graphene.String(), issuer=graphene.String())

    def resolve_lti_course(self, info, **kwargs):
        badge_class_id = kwargs.get('badge_class_id')
        if badge_class_id:
            return LtiCourse.objects.filter(badgeclass__entity_id=badge_class_id).first()
        return None

    def resolve_lti_tool(self, info, **kwargs):
        client_id = kwargs.get('client_id')
        issuer = kwargs.get('issuer')
        if client_id and issuer:
            return LtiTool.objects.filter(client_id=client_id, issuer=issuer).first()
        return None
