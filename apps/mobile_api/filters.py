import django_filters as filters
from django.db.models import Q

from issuer.models import BadgeClass

class CatalogBadgeClassFilter(filters.FilterSet):
    name = filters.CharFilter(field_name='name', lookup_expr='icontains')
    institution = filters.CharFilter(
        field_name='issuer__faculty__institution__entity_id'
    )
    is_micro = filters.BooleanFilter(field_name='is_micro_credentials')

    q = filters.CharFilter(method='filter_q', label='Search')

    class Meta:
        model = BadgeClass
        fields = ['name', 'institution', 'is_micro', 'q']

    def filter_q(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(issuer__name_english__icontains=value) |
            Q(issuer__name_dutch__icontains=value) |
            Q(issuer__faculty__name_english__icontains=value) |
            Q(issuer__faculty__name_dutch__icontains=value) |
            Q(issuer__faculty__institution__name_english__icontains=value) |
            Q(issuer__faculty__institution__name_dutch__icontains=value)
        )
