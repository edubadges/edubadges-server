from django.urls import path
from mainsite.auditlog_views import UnifiedAuditLogView

urlpatterns = [
    path('', UnifiedAuditLogView.as_view(), name='unified_auditlog'),
]
