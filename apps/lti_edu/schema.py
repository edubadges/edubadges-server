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

    def resolve_enrollments(self, info, **kwargs):
        return StudentsEnrolled.objects.filter(user=info.context.user)
