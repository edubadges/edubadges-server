import AuditLogPagination
from badgrsocialauth.permissions import IsSuperUser
from django.db.models import Count
from entity.api import BaseEntityView
from institution.models import Faculty, Institution
from institution.serializers import FacultyAuditLogSerializer, InstitutionAuditLogSerializer
from issuer.models import BadgeClass, Issuer
from issuer.serializers import BadgeClassAuditLogSerializer, IssuerAuditLogSerializer
from rest_framework.response import Response
from staff.models import BadgeClassStaff, FacultyStaff, InstitutionStaff, IssuerStaff
from staff.serializers import (
    BadgeClassStaffAuditLogSerializer,
    FacultyStaffAuditLogSerializer,
    InstitutionStaffAuditLogSerializer,
    IssuerStaffAuditLogSerializer,
)


class UnifiedAuditLogView(BaseEntityView):
    """
    Unified audit log endpoint for all entity types.

    Usage:
        GET /api/v2/auditlog?entity_type=institution&page=1&page_size=50

    Supported entity_type values:
        - institution
        - faculty
        - issuer
        - badgeclass
        - institution_staff
        - faculty_staff
        - issuer_staff
        - badgeclass_staff

    Query parameters:
        - entity_type: Required. The type of entity to retrieve audit logs for
        - page: Optional. Page number (default: 1)
        - page_size: Optional. Number of items per page (default: 50, max: 200)

    Response format:
        {
            "count": <total number of items>,
            "next": "<url to next page>",
            "previous": "<url to previous page>",
            "results": [
                {
                    "id": <history entry id>,
                    "action": <create/update/delete>,
                    "timestamp": <ISO timestamp>,
                    "updated_by": <username>,
                    "changes": <dict of changed fields>,
                    ...
                }
            ]
        }
    """

    permission_classes = (IsSuperUser,)
    pagination_class = AuditLogPagination

    def get_model_mapping(self):
        return {
            'institution': {
                'model': Institution,
                'serializer': InstitutionAuditLogSerializer,
            },
            'faculty': {
                'model': Faculty,
                'serializer': FacultyAuditLogSerializer,
            },
            'issuer': {
                'model': Issuer,
                'serializer': IssuerAuditLogSerializer,
            },
            'badgeclass': {
                'model': BadgeClass,
                'serializer': BadgeClassAuditLogSerializer,
            },
            'institution_staff': {
                'model': InstitutionStaff,
                'serializer': InstitutionStaffAuditLogSerializer,
            },
            'faculty_staff': {
                'model': FacultyStaff,
                'serializer': FacultyStaffAuditLogSerializer,
            },
            'issuer_staff': {
                'model': IssuerStaff,
                'serializer': IssuerStaffAuditLogSerializer,
            },
            'badgeclass_staff': {
                'model': BadgeClassStaff,
                'serializer': BadgeClassStaffAuditLogSerializer,
            },
        }

    def get_model_and_serializer(self, entity_type):
        model_mapping = self.get_model_mapping()
        if entity_type not in model_mapping:
            return None, None

        config = model_mapping[entity_type]
        return config['model'], config['serializer']

    def get(self, request, **kwargs):
        entity_type = request.query_params.get('entity_type')

        if not entity_type:
            model_mapping = self.get_model_mapping()
            return Response(
                {'error': 'entity_type parameter is required', 'valid_options': list(model_mapping.keys())}, status=400
            )

        model_class, serializer_class = self.get_model_and_serializer(entity_type)

        if not model_class or not serializer_class:
            model_mapping = self.get_model_mapping()
            return Response(
                {'error': f'Invalid entity_type. Valid options: {", ".join(model_mapping.keys())}'}, status=400
            )

        queryset = (
            model_class.objects.annotate(history_count=Count('history'))
            .filter(history_count__gt=0)
            .select_related('updated_by')
        )

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = serializer_class(page, many=True)
            flat_history = [history_item for obj in serializer.data for history_item in obj['history']]
            return paginator.get_paginated_response(flat_history)

        serializer = serializer_class(queryset, many=True)
        flat_history = [history_item for obj in serializer.data for history_item in obj['history']]

        return Response(flat_history)
