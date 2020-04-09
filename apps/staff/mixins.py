class PermissionedModelMixin(object):
    """
    Abstract class used for inheritance by all the Models (Badgeclass, Issuer, Faculty & Institution that have a related
    Staff model. Used for retrieving permissions and staff members.
    """

    def _get_local_permissions(self, user):
        """
        :param user: BadgeUser (teacher)
        :return: a permissions dictionary for the instance only, without looking higher in the hierarchy.
        """
        staff = self.get_staff_member(user)
        if staff:
            return staff.permissions
        else:
            return None

    def check_local_permissions(self, user, required_permissions):
        """
        This checks if user has all the given permissions on this object
        :param user: BadgeUser (teacher)
        :param required_permissions: a list of strings
        :return: Boolean
        """
        user_permissions = self._get_local_permissions(user)
        if user_permissions:
            perm_count = 0
            for perm in required_permissions:
                if user_permissions[perm]:
                    perm_count += 1
            return perm_count == len(required_permissions)
        return False

    def get_permissions(self, user):
        """
        This method returns (inherited or local) permissions for the instance by climbing the permission tree.
        :param user: BadgeUser (teacher)
        :return: a permissions dictionary
        """
        try:
            parent_perms = self.parent.get_permissions(user)
            local_perms = self._get_local_permissions(user)
            if not parent_perms:
                return local_perms
            elif not local_perms:
                return parent_perms
            else:
                combined_perms = {}
                for key in local_perms:
                    combined_perms[key] = local_perms[key] if local_perms[key] > parent_perms[key] else parent_perms[key]
                return combined_perms
        except AttributeError:  # recursive base case
            return self._get_local_permissions(user)

    def has_permissions(self, user, permissions):
        """
        This method checks to see if a user has all the given permissions on an object
        :param user: BadgeUser (teacher)
        :param permissions: a list of strings
        :return: True if user has all the permissions
        """
        user_perms = self.get_permissions(user)
        perm_count = 0
        if not user_perms:
            return False
        else:
            for perm in permissions:
                if not user_perms[perm]:
                    return False
                else:
                    perm_count += 1
            return len(permissions) == perm_count

    @property
    def staff_items(self):
        return self.cached_staff()

    def get_local_staff_members(self, permissions=None):
        """
        gets the staff members belonging to this object that have all of the permissions given
        :param permissions: array of permissions required
        :return: list of staff memberships that have this
        """
        result = []
        if permissions:
            for staff in self.staff_items:
                has_perms = []
                for perm in permissions:
                    if staff.permissions[perm]:
                        has_perms.append(perm)
                if len(has_perms) == len(permissions):
                    result.append(staff)
            return result
        else:
            return self.staff_items

    def get_staff_member(self, user):
        """
        Get a staff membership object belonging to the given user.
        :param user: BadgeUser (teacher)
        :return: Staff object
        """
        for staff in self.staff_items:
            if staff.user == user:
                return staff

    def publish(self, *args, **kwargs):
        super(PermissionedModelMixin, self).publish(*args, **kwargs)
        for member in self.cached_staff():
            member.cached_user.publish()
