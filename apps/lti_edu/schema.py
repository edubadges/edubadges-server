import graphene
from graphene_django.types import DjangoObjectType
from .models import StudentsEnrolled


class StudentsEnrolledType(DjangoObjectType):

    class Meta:
        model = StudentsEnrolled
        fields = ('entity_id', 'badge_class', 'date_created', 'date_consent_given',
                  'user', 'badge_instance', 'date_awarded', 'denied')


class Query(object):

    enrollments = graphene.List(StudentsEnrolledType)

    def resolve_enrollments(self, info, **kwargs):
        badge_classes = info.context.user.get_all_badgeclasses_with_permissions(['may_award'])
        enrollments = []
        for bc in badge_classes:
            enrollments += bc.cached_enrollments()
        return enrollments