import graphene

from django.contrib.contenttypes.models import ContentType
from graphene.types.json import JSONString
from graphene_django.types import DjangoObjectType

from badgeuser.models import UserProvisionment
from mainsite.exceptions import GraphQLException
from staff.schema import PermissionType


def resolver_blocker_for_students(f):
    """Decorator to block students from using graphql resolver functions"""
    def wrapper(*args, **kwargs):
        info = args[1]
        if not hasattr(info.context.user, 'is_teacher') and not info.context.user.is_teacher:
            raise GraphQLException('Student may not retrieve {} of {}'.format(info.field_name, info.parent_type))
        return f(*args, **kwargs)
    return wrapper


def resolver_blocker_only_for_current_user(f):
    """Decorator for BadgeUserType for fields allowed only for the current user"""
    def wrapper(*args):
        instance = args[0]
        info = args[1]
        if info.context.user is not instance:
            raise GraphQLException('This call is only for the current user')
        return f(*args)
    return wrapper


class JSONType(JSONString):
    @staticmethod
    def serialize(dt):
        return dt


class ContentTypeType(DjangoObjectType):
    class Meta:
        model = ContentType
        fields = ('id',)


class UserProvisionmentType(DjangoObjectType):

    class Meta:
        model = UserProvisionment
        fields = ('email', 'entity_id', 'content_type', 'object_id', 'data', 'for_teacher', 'rejected', 'created_at')

    content_type = graphene.Field(ContentTypeType)
    data = graphene.Field(JSONType)


class UserProvisionmentResolverMixin(object):

    userprovisionments = graphene.List(UserProvisionmentType)

    def resolve_userprovisionments(self, info):
        return self.cached_userprovisionments()



class ContentTypeIdResolverMixin(object):
    content_type_id = graphene.Field(graphene.Int)

    def resolve_content_type_id(self, info):
        return ContentType.objects.get_for_model(self).pk


class PermissionsResolverMixin(object):
    """
    Schema mixin to resolve entity permissions
    """

    permissions = graphene.Field(PermissionType)

    @resolver_blocker_for_students
    def resolve_permissions(self, info):
        return self.get_permissions(info.context.user)


class DefaultLanguageResolverMixin(object):
    """
    Schema mixin to resolve default language
    """

    default_language = graphene.String()

    @resolver_blocker_for_students
    def resolve_default_language(self, info):
        return self.default_language


class ImageResolverMixin(object):
    """
    Schema mixin to resolve image property
    """
    def resolve_image(self, info):
        return self.image_url()


class StaffResolverMixin(object):

    @resolver_blocker_for_students
    def resolve_staff(self, info):
        if self.has_permissions(info.context.user, ['may_read']):
            return self.staff_items
        else:
            return []
