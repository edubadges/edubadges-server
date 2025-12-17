from badgrsocialauth.permissions import IsSuperUser
from django.db.models import Count
from entity.api import BaseEntityView
from rest_framework import serializers
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class AuditLogPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class BaseAuditLogSerializer(serializers.Serializer):
    history = serializers.SerializerMethodField()

    def get_history(self, obj):
        updated_by = obj.updated_by.username if obj.updated_by else None
        history_items = obj.history.values()

        return [
            {
                **item,
                'updated_by': updated_by,
            }
            for item in history_items
        ]


class BaseAuditLogView(BaseEntityView):
    permission_classes = (IsSuperUser,)
    pagination_class = AuditLogPagination
    serializer_class = None
    model = None

    def get_queryset(self):
        return (
            self.model.objects.annotate(history_count=Count('history'))
            .filter(history_count__gt=0)
            .select_related('updated_by')
        )

    def get(self, request, **kwargs):
        queryset = self.get_queryset()

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = self.serializer_class(page, many=True)
            flat_history = [history_item for obj in serializer.data for history_item in obj['history']]
            return paginator.get_paginated_response(flat_history)

        serializer = self.serializer_class(queryset, many=True)
        flat_history = [history_item for obj in serializer.data for history_item in obj['history']]

        return Response(flat_history)
