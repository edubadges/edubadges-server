# Audit Log API Documentation

This document describes the audit log API endpoints for tracking changes to entities in the edubadges system.

## Overview

The audit log system tracks changes to the following entities:

- Institution
- Faculty
- Issuer
- BadgeClass
- InstitutionStaff
- FacultyStaff
- IssuerStaff
- BadgeClassStaff

All audit log endpoints require superuser permissions and support server-side pagination.

## API Endpoints

### 1. Unified Audit Log Endpoint (Recommended)

**Endpoint:** `GET /auditlog/?entity_type=<type>&page=<page>&page_size=<size>`

This single endpoint provides access to audit logs for all entity types.

**Query Parameters:**

- `entity_type` (required): The type of entity to retrieve audit logs for
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: 50, max: 200)

**Valid entity_type values:**

- `institution`
- `faculty`
- `issuer`
- `badgeclass`
- `institution_staff`
- `faculty_staff`
- `issuer_staff`
- `badgeclass_staff`

**Example Requests:**

```bash
# Get institution audit logs
GET /auditlog/?entity_type=institution&page=1&page_size=50

# Get badgeclass staff audit logs
GET /auditlog/?entity_type=badgeclass_staff&page=2&page_size=100
```

**Response Format:**

```json
{
  "count": 150,
  "next": "http://localhost:8000/auditlog/?entity_type=institution&page=2&page_size=50",
  "previous": null,
  "results": [
    {
      "id": 123,
      "action": 0,
      "timestamp": "2025-12-17T10:30:00.000000Z",
      "updated_by": "admin",
      "object_id": 456,
      "object_repr": "Example Institution",
      "changes": "{\"name_english\": [\"Old Name\", \"New Name\"]}",
      "additional_data": null,
      ...
    }
  ]
}
```

### 2. Individual Entity Audit Log Endpoints

For convenience, each entity type also has its own dedicated endpoint.

#### Institution Endpoints

**BadgeClass Audit Log:**

```
GET /issuer/badgeclasses/auditlog
```

**Issuer Audit Log:**

```
GET /issuer/auditlog
```

**Institution Audit Log:**

```
GET /institution/auditlog
```

**Faculty Audit Log:**

```
GET /institution/faculties/auditlog
```

#### Staff Endpoints

**InstitutionStaff Audit Log:**

```
GET /staff-membership/institution/auditlog
```

**FacultyStaff Audit Log:**

```
GET /staff-membership/faculty/auditlog
```

**IssuerStaff Audit Log:**

```
GET /staff-membership/issuer/auditlog
```

**BadgeClassStaff Audit Log:**

```
GET /staff-membership/badgeclass/auditlog
```

**Pagination Parameters:**
All individual endpoints support the same pagination parameters:

- `page` (optional): Page number (default: 1)
- `page_size` (optional): Number of items per page (default: 50, max: 200)

## Response Fields

Each audit log entry contains the following fields:

- `id`: Unique identifier for the audit log entry
- `action`: Action type (0=create, 1=update, 2=delete)
- `timestamp`: ISO 8601 timestamp of when the change occurred
- `updated_by`: Username of the user who made the change (or null if system)
- `object_id`: ID of the entity that was modified
- `object_repr`: String representation of the entity
- `changes`: JSON string containing the changed fields and their before/after values
- `additional_data`: Any additional metadata about the change

## Implementation Details

### Models

All tracked models have been updated with the `AuditlogHistoryField`:

```python
from auditlog.models import AuditlogHistoryField

class Institution(BaseVersionedEntity):
    history = AuditlogHistoryField()
    # ... other fields
```

### Pagination

The API uses Django REST Framework's `PageNumberPagination` with:

- Default page size: 50 items
- Maximum page size: 200 items
- Configurable via `page_size` query parameter

### Permissions

All audit log endpoints require:

- User must be authenticated
- User must have superuser permissions (`IsSuperUser` permission class)

### Architecture

The implementation follows a clean architecture pattern:

1. **Base Classes** (`apps/mainsite/auditlog_api.py`):

   - `BaseAuditLogSerializer`: Base serializer for all audit log entries
   - `BaseAuditLogView`: Base view for individual entity audit logs
   - `AuditLogPagination`: Pagination configuration

2. **Concrete Implementation** (`apps/mainsite/auditlog_views.py`):

   - `UnifiedAuditLogView`: Unified endpoint implementation

3. **Entity-Specific Views**:
   - Each entity has its own view class (e.g., `InstitutionAuditLog`, `BadgeClassAuditLog`)
   - All inherit from `BaseAuditLogView` for consistent behavior

## Usage Examples

### Example 1: Get all institution changes

```bash
curl -X GET 'http://localhost:8000/auditlog/?entity_type=institution&page_size=100' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Example 2: Get badgeclass audit logs (paginated)

```bash
curl -X GET 'http://localhost:8000/issuer/badgeclasses/auditlog?page=1&page_size=50' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

### Example 3: Get staff membership changes

```bash
curl -X GET 'http://localhost:8000/auditlog/?entity_type=institution_staff' \
  -H 'Authorization: Bearer YOUR_TOKEN'
```

## Extending the API

To add audit logging to a new model:

1. Add the history field to the model:

```python
from auditlog.models import AuditlogHistoryField

class MyModel(BaseVersionedEntity):
    history = AuditlogHistoryField()
```

2. Register the model with auditlog:

```python
from auditlog.registry import auditlog
auditlog.register(MyModel)
```

3. Create a serializer:

```python
from mainsite.auditlog_api import BaseAuditLogSerializer

class MyModelAuditLogSerializer(BaseAuditLogSerializer):
    class Meta:
        model = MyModel
        fields = ['history']
```

4. Create a view:

```python
from mainsite.auditlog_api import BaseAuditLogView

class MyModelAuditLog(BaseAuditLogView):
    model = MyModel
    serializer_class = MyModelAuditLogSerializer
```

5. Add URL routing:

```python
path('mymodel/auditlog', MyModelAuditLog.as_view(), name='mymodel_auditlog'),
```

6. Add to unified endpoint (optional):
   Update the `get_model_mapping()` method in `AllEntitiesAuditLogView` to include your model.

## Notes

- Audit logs are automatically created by the django-auditlog package
- Only entities with at least one history entry are returned
- The `updated_by` field is populated from the entity's `updated_by` foreign key
- History entries are flattened from the parent entity to provide a flat list of changes
- All timestamps are in UTC
