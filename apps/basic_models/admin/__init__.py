from django.contrib.admin import site as admin_site

from basic_models.actions import ToggleActive, DeleteRequiresPermission
from .admin import CreatedUpdatedBy, LocalPreview, AutoGroupMeta


class site(object):

    @staticmethod
    def add_base(admin_class, base):
        if base not in admin_class.__bases__:
            admin_class.__bases__ = (base,) + admin_class.__bases__

    @staticmethod
    def register(model, admin_class):
        def _list_has_all_values(superset, subset):
            return all([value in superset for value in subset])

        field_names = [field.name for field in model._meta.fields]

        if _list_has_all_values(field_names, ('created_by', 'updated_by')):
            site.add_base(admin_class, CreatedUpdatedBy)

        if 'is_active' in field_names:
            site.add_base(admin_class, LocalPreview)
            site.add_base(admin_class, ToggleActive)
            site.add_base(admin_class, DeleteRequiresPermission)

        site.add_base(admin_class, AutoGroupMeta)

        admin_site.register(model, admin_class)
