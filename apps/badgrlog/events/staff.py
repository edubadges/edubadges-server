from .base import BaseBadgrEvent


class BasePermissionEvent(BaseBadgrEvent):

    def __init__(self, staff_instance, request):
        self.staff_instance = staff_instance
        self.request = request

    def to_representation(self):
        return {
            'creator_id': self.request.user.id,
            'creator_name': self.request.user.full_name,
            'staff_id': self.staff_instance.id,
            'staff_member_id': self.staff_instance.user.id,
            'staff_member_name': self.staff_instance.user.full_name,
            'staff_object_type': self.staff_instance.object.__class__.__name__,
            'staff_object_id': self.staff_instance.object.id,
            'staff_object_name': self.staff_instance.object.name,
            'permissions': self.staff_instance.permissions
        }


class PermissionChangedEvent(BasePermissionEvent):

    def __init__(self, staff_instance, previous_permissions, request):
        self.previous_permissions = previous_permissions
        super(PermissionChangedEvent, self).__init__(staff_instance, request)

    def to_representation(self):
        d = super(PermissionChangedEvent, self).to_representation()
        d['previous_permissions'] = self.previous_permissions
        return d


class PermissionCreatedEvent(BasePermissionEvent):
    pass


class PermissionDeletedEvent(BasePermissionEvent):
    pass
