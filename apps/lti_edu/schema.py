import graphene
from graphene_django.types import DjangoObjectType

from .models import StudentsEnrolled


class StudentsEnrolledType(DjangoObjectType):
    class Meta:
        model = StudentsEnrolled
        fields = ('date_created', 'date_consent_given', 'date_awarded', 'badge_class', 'denied',
                  'user', 'badge_instance', 'entity_id')


class Query(object):
    enrollments = graphene.List(StudentsEnrolledType)
    enrollment = graphene.Field(StudentsEnrolledType, id=graphene.String())

    def resolve_enrollments(self, info, **kwargs):
        return StudentsEnrolled.objects.filter(user=info.context.user)

    def resolve_enrollment(self, info, **kwargs):
        id = kwargs.get('id')
        if id is not None:
            return StudentsEnrolled.objects.get(entity_id=id, user=info.context.user)
