import graphene
from graphene_django.types import DjangoObjectType
from .models import Institution, Faculty

class InstitutionType(DjangoObjectType):
    class Meta:
        model = Institution

class FacultyType(DjangoObjectType):
    class Meta:
        model = Faculty

class Query(object):
    institutions = graphene.List(InstitutionType)
    def resolve_institutions(self, info, **kwargs):
        return Institution.objects.all()

    institution = graphene.Field(InstitutionType, id=graphene.ID())
    def resolve_institution(self, info, **kwargs):
        id = kwargs.get('id')

        if id is not None:
            return Institution.objects.get(id=id)

        return None

    faculties = graphene.List(FacultyType)
    def resolve_faculties(self, info, **kwargs):
        return Faculty.objects.all()

    faculty = graphene.Field(FacultyType, id=graphene.ID())
    def resolve_faculty(self, info, **kwargs):
        id =  kwargs.get('id')

        if id is not None:
            return Faculty.objects.get(id=id)

        return None