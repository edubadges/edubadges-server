import django_filters as filters

from issuer.models import BadgeClass

INSTITUTION_TYPE_FILTER_CHOICES = [
    ('MBO', 'MBO'),
    ('HBO', 'HBO'),
    ('WO', 'WO'),
]

class CatalogBadgeClassFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    institution = filters.CharFilter(
        field_name='issuer__faculty__institution__entity_id',
    )
    institution_type = filters.ChoiceFilter(
        field_name='issuer__faculty__institution__institution_type',
        choices=INSTITUTION_TYPE_FILTER_CHOICES,
        help_text="Filter by institution type. Omit this parameter to include all types.",
    )

    class Meta:
        model = BadgeClass
        fields = ['name', 'institution', 'institution_type']
