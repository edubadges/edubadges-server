from copy import deepcopy

from django.utils.translation import ugettext_lazy as _lazy, ugettext as _
from django.contrib.admin.utils import model_ngettext as model_verbose_name


class Clone(object):
    actions = ['clone']

    def clone(self, request, queryset):

        def _clone(instance, save=True):
            new_instance = deepcopy(instance)
            new_instance.id = None
            if save:
                new_instance.save()
            return new_instance

        for instance in queryset:
            # Clone a new instance
            new_instance = _clone(instance)

            # Get reverse relations to this instance
            reverse_relations = instance._meta.get_all_related_objects() + \
                instance._meta.get_all_related_many_to_many_objects()

            # Get related instances (relation_meta is a RelatedObject instance)
            for relation_meta in reverse_relations:
                related_instances = \
                    getattr(instance, relation_meta.get_accessor_name()).all()

                # Clone, and relate each related instance to the new instance
                for related_instance in related_instances:
                    new_related_instance = _clone(related_instance, save=False)
                    setattr(new_related_instance, relation_meta.field.name,
                            new_instance)
                    new_related_instance.save()

    clone.short_description = \
        _lazy("Clone selected %(verbose_name_plural)s and related instances")


class ToggleActive(object):
    actions = ['is_active_true', 'is_active_false']

    def _set_is_active(self, is_active, request, queryset):
        count = queryset.update(is_active=is_active)
        self.message_user(
            request, _("Successfully %(prefix)sactivated %(count)d %(items)s.")
            % {
                "count": count,
                "items": model_verbose_name(self.opts, count),
                "prefix": "de" if not is_active else "",
            })

    def is_active_true(self, *args):
        self._set_is_active(True, *args)

    def is_active_false(self, *args):
        self._set_is_active(False, *args)

    is_active_true.short_description = \
        "Activate selected %(verbose_name_plural)s"
    is_active_false.short_description = \
        "De-activate selected %(verbose_name_plural)s"


class HideToggleActive(object):
    def get_actions(self, request):
        actions = super(HideToggleActive, self).get_actions(request)
        try:
            del actions['is_active_true']
            del actions['is_active_false']
        except KeyError:
            pass
        return actions


class DeleteRequiresPermission(object):

    def get_actions(self, request):
        actions = super(DeleteRequiresPermission, self).get_actions(request)
        if not self.has_delete_permission(request):
            try:
                del actions['delete_selected']
            except KeyError:
                pass
        return actions
