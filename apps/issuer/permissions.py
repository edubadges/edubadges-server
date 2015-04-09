from rest_framework import permissions
import rules

SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS']


@rules.predicate
def is_owner(user, component):
    return user == component.owner


@rules.predicate
def is_editor(user, issuer):
    return issuer.editors.filter(pk=user.pk).exists()


@rules.predicate
def is_staff(user, issuer):
    return issuer.staff.filter(pk=user.pk).exists()

is_on_staff = is_owner | is_staff
is_staff_editor = is_owner | is_editor

rules.add_perm('issuer.is_owner', is_owner)
rules.add_perm('issuer.is_editor', is_staff_editor)
rules.add_perm('issuer.is_staff', is_on_staff)


@rules.predicate
def is_badgeclass_editor(user, badgeclass):
    return badgeclass.issuer.editors.filter(pk=user.pk).exists()


@rules.predicate
def is_badgeclass_staff(user, badgeclass):
    return badgeclass.issuer.staff_set.filter(pk=user.pk).exists()

can_issue_badgeclass = is_owner | is_badgeclass_staff
can_edit_badgeclass = is_owner | is_badgeclass_editor

rules.add_perm('issuer.can_issue_badge', can_issue_badgeclass)
rules.add_perm('issuer.can_edit_badgeclass', can_edit_badgeclass)


class MayIssueBadgeClass(permissions.BasePermission):
    """
    Allows those who have been given permission to issue badges on an Issuer to create
    IssuerAssertions from its IssuerBadgeClasses
    ---
    model: BadgeClass
    """

    def has_object_permission(self, request, view, badgeclass):
        return request.user.has_perm('issuer.can_issue_badge', badgeclass)


class MayEditBadgeClass(permissions.BasePermission):
    """
    Request.user is authorized to perform safe operations on a BadgeClass
    if they are on its issuer's staff. They may perform unsafe operations
    on a BadgeClass if they are among its issuers' editors.
    ---
    model: BadgeClass
    """

    def has_object_permission(self, request, view, badgeclass):
        if request.method in SAFE_METHODS:
            return request.user.has_perm('issuer.can_issue_badge', badgeclass)
        else:
            return request.user.has_perm('issuer.can_edit_badgeclass', badgeclass)


class IsOwnerOrStaff(permissions.BasePermission):
    """
    Ensures request user is owner for unsafe operations, or at least
    staff for safe operations.
    """
    def has_object_permission(self, request, view, issuer):
        if request.method in SAFE_METHODS:
            return request.user.has_perm('issuer.is_staff', issuer)
        else:
            return request.user.has_perm('issuer.is_owner', issuer)


class IsEditor(permissions.BasePermission):
    """
    Request.user is authorized to perform safe operations if they are staff or
    perform unsafe operations if they are owner or editor of an issuer.
    ---
    model: Issuer
    """

    def has_object_permission(self, request, view, issuer):
        if request.method in SAFE_METHODS:
            return request.user.has_perm('issuer.is_staff', issuer)
        else:
            return request.user.has_perm('issuer.is_editor', issuer)


class IsStaff(permissions.BasePermission):
    """
    Request user is authorized to perform operations if they are owner or on staff
    of an Issuer.
    ---
    model: Issuer
    """
    def has_object_permission(self, request, view, issuer):
        return request.user.has_perm('issuer.is_staff', issuer)
