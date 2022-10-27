from django.contrib.admin import ModelAdmin
from django.db import transaction
from django.utils.translation import ugettext_lazy, ugettext as _
from django.contrib.admin.utils import model_ngettext


class CreatedUpdatedBy(ModelAdmin):
    readonly_fields = ('created_by', 'updated_by')

    @staticmethod
    def _populate_created_and_updated_by(instance, user):
        if not instance.pk:
            instance.created_by = user
        instance.updated_by = user

    def save_model(self, request, obj, form, change):
        instance = form.save(commit=False)
        self._populate_created_and_updated_by(instance, request.user)
        instance.save()
        return instance

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            self._populate_created_and_updated_by(instance, request.user)
            instance.save()
        formset.save_m2m()


class AutoGroupMeta(ModelAdmin):

    def get_form(self, request, obj=None, **kwargs):
        ModelForm = super(AutoGroupMeta, self).get_form(request, obj, **kwargs)
        return ModelForm

    def get_readonly_fields(self, request, obj=None):
        readonly_fields = list(getattr(self, 'readonly_fields', []))
        if obj:
            readonly_fields += ['created_by', 'updated_by',
                                'created_at', 'updated_at']

            fields_which_exist = [field for field in readonly_fields if hasattr(obj, field)]

            return fields_which_exist
        else:
            return readonly_fields

    def get_fieldsets(self, request, obj=None):
        fieldsets = super(AutoGroupMeta, self).get_fieldsets(request, obj)
        meta_fields = ('is_active', 'created_at', 'created_by',
                       'updated_at', 'updated_by')
        meta_grouped = []

        # Remove Meta fields from any defined fieldsets
        for fieldset in fieldsets:
            key, field_options = fieldset
            field_options['fields'] = [field_name for field_name in field_options['fields'] if field_name not in meta_fields]
            meta_grouped.append((key, field_options))

        # Add meta fields (if they exist on the instance) to a Meta fieldset
        exclude = self.exclude or []
        fields = [field for field in meta_fields if hasattr(obj, field) and field not in exclude]

        if fields:
            meta_grouped.append(
                ('Meta', {'fields': fields, 'classes': ('collapse',)})
            )

        return meta_grouped


class LocalPreview(ModelAdmin):
    change_form_template = "admin/change_form_with_local_preview.html"

class UserModelAdmin(ModelAdmin):
    """ModelAdmin subclass that will automatically update created_by and updated_by fields"""
    save_on_top = True
    readonly_fields = ('created_by', 'updated_by')

    def save_model(self, request, obj, form, change):
        instance = form.save(commit=False)
        self._update_instance(instance, request.user)
        instance.save()
        return instance

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)

        try:
            # For Django 1.7+
            for obj in formset.deleted_objects:
                obj.delete()
        except AssertionError:
            # Django 1.6 and earlier already deletes the objects, trying to
            # delete them a second time raises an AssertionError.
            pass

        for instance in instances:
            self._update_instance(instance, request.user)
            instance.save()
        formset.save_m2m()

    @staticmethod
    def _update_instance(instance, user):
        if not instance.pk:
            instance.created_by = user
        instance.updated_by = user


class ActiveModelAdmin(ModelAdmin):
    """ModelAdmin subclass that adds activate and delete actions and situationally removes the delete action"""
    actions = ['activate_objects', 'deactivate_objects']

    @transaction.atomic
    def _set_objects_active(self, request, queryset, active):
        """ Sets the 'is_active' property of each item in ``queryset`` to ``active`` and reports success to the user. """
        # We call save on each object instead of using queryset.update to allow for custom save methods and hooks.
        count = 0
        for obj in queryset.select_for_update():
            obj.is_active = active
            obj.save(update_fields=['is_active'])
            count += 1
        self.message_user(request, _("Successfully %(prefix)sactivated %(count)d %(items)s.") % {
            "prefix": "" if active else "de", "count": count, "items": model_ngettext(self.opts, count)
        })

    def activate_objects(self, request, queryset):
        """Admin action to set is_active=True on objects"""
        self._set_objects_active(request, queryset, True)
    activate_objects.short_description = "Activate selected %(verbose_name_plural)s"

    def deactivate_objects(self, request, queryset):
        """Admin action to set is_active=False on objects"""
        self._set_objects_active(request, queryset, False)
    deactivate_objects.short_description = "Deactivate selected %(verbose_name_plural)s"

    def get_actions(self, request):
        actions = super(ActiveModelAdmin, self).get_actions(request)
        if not self.has_delete_permission(request):
            if 'delete_selected' in actions:
                del actions['delete_selected']
        return actions


class TimestampedModelAdmin(ModelAdmin):
    """ModelAdmin subclass that will set created_at and updated_at fields to readonly"""
    readonly_fields = ('created_at', 'updated_at')


class DefaultModelAdmin(ActiveModelAdmin, UserModelAdmin, TimestampedModelAdmin):
    """ModelAdmin subclass that combines functionality of UserModel, ActiveModel, and TimestampedModel admins and defines a Meta fieldset"""
    readonly_fields = ('created_at', 'created_by', 'updated_at', 'updated_by')
    fieldsets = (
        ('Meta', {'fields': ('is_active', 'created_at', 'created_by', 'updated_at', 'updated_by'), 'classes': ('collapse',)}),
    )


class SlugModelAdmin(DefaultModelAdmin):
    prepopulated_fields = {"slug": ("name",)}
    list_display = ('name', 'slug', 'is_active')
    fieldsets = (
        (None, {'fields': ('name', 'slug')}),
    ) + DefaultModelAdmin.fieldsets


class OneActiveAdmin(ModelAdmin):
    save_on_top = True
    list_display = ('__unicode__', 'is_active')
    change_form_template = "admin/preview_change_form.html"
    actions = ['duplicate']

    def duplicate(self, request, queryset):
        for object in queryset:
            object.clone()
        duplicate.short_description = ugettext_lazy("Duplicate selected %(verbose_name_plural)s")