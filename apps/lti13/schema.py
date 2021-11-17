import graphene
from graphene_django.types import DjangoObjectType

from .models import LtiCourse


class LtiCourseType(DjangoObjectType):
    class Meta:
        model = LtiCourse
        fields = ('entity_id', 'created_at', 'identifier', 'title')


class Query(object):
    lti_course = graphene.Field(LtiCourseType, badge_class_id=graphene.String())

    def resolve_lti_course(self, info, **kwargs):
        badge_class_id = kwargs.get('badge_class_id')
        if badge_class_id:
            return LtiCourse.objects \
                .filter(badgeclass__entity_id=badge_class_id).first()
        return None
