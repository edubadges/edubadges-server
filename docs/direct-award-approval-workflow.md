# Direct Award Approval Workflow

## Overview

This document describes the new direct award approval workflow that allows institution administrators to review and approve direct award requests before they are sent to recipients. This system helps prevent abuse and ensures appropriate use of the direct awarding system.

## Features

### 1. Approval Workflow

- **Optional Approval**: Direct awards can be marked as requiring approval during creation
- **Pending State**: Awards requiring approval are created with `STATUS_PENDING_APPROVAL`
- **Admin Review**: Institution admins can approve or reject pending awards
- **Status Tracking**: Full audit trail of approval decisions with timestamps and reasons

### 2. Threshold Monitoring

- **Automatic Detection**: System monitors for suspicious activity patterns
- **Configurable Thresholds**: Set limits on awards per time period
- **Admin Notifications**: Alerts when potential abuse is detected

### 3. Notification System

- **Creator Notifications**: Email alerts when awards are approved or rejected
- **Admin Alerts**: Notifications about pending approvals and threshold violations
- **Detailed Information**: Notifications include reasons and comments

## API Changes

### New Endpoints

#### GET `/directaward/pending-approvals`

Lists all direct awards pending approval for the user's institution.

**Response:**
```json
{
  "pending_approvals": [
    {
      "entity_id": "da-001",
      "recipient_email": "student@example.edu",
      "eppn": "student123",
      "badgeclass_name": "Introduction to Python",
      "created_at": "2025-01-15T10:30:00Z",
      "created_by": "teacher@example.edu"
    }
  ]
}
```

#### POST `/directaward/approval/{entity_id}`

Approve or reject a direct award.

**Request (Approve):**
```json
{
  "action": "approve",
  "comments": "This award is appropriate"
}
```

**Request (Reject):**
```json
{
  "action": "reject",
  "rejection_reason": "Too many similar awards",
  "comments": "Student already has 5 awards in this category"
}
```

**Response:**
```json
{
  "result": "ok",
  "status": "Approved",
  "approval_record": {
    "status": "Approved",
    "reviewed_by": "admin@example.edu",
    "review_date": "2025-01-15T11:00:00Z",
    "comments": "Looks good"
  }
}
```

### Enhanced Bundle Creation

The existing bundle creation endpoint now supports an optional `requires_approval` field:

```json
{
  "badgeclass": "badgeclass-123",
  "direct_awards": [{"eppn": "student@example.edu", "recipient_email": "student@example.edu"}],
  "requires_approval": true,
  "batch_mode": true,
  "identifier_type": "eppn",
  "notify_recipients": false
}
```

### Enhanced Bundle Details

The bundle detail response now includes approval information:

```json
{
  "direct_award_pending_approval_count": 2,
  "direct_award_approved_count": 5,
  "direct_awards": [
    {
      "recipient_email": "user@example.edu",
      "eppn": "user123",
      "status": "Pending Approval",
      "entity_id": "da-001",
      "approval_status": "Pending",
      "approval_comments": null,
      "rejection_reason": null
    }
  ]
}
```

## Database Changes

### New Models

#### `DirectAwardApproval`

```python
class DirectAwardApproval(models.Model):
    STATUS_PENDING = 'Pending'
    STATUS_APPROVED = 'Approved'
    STATUS_REJECTED = 'Rejected'
    
    direct_award = models.OneToOneField('directaward.DirectAward', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    review_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

### Modified Models

#### `DirectAward`

Added new statuses:
- `STATUS_PENDING_APPROVAL = 'Pending Approval'`
- `STATUS_APPROVED = 'Approved'`

Added methods:
- `request_approval()`: Set award as pending approval
- `approve(reviewer, comments)`: Approve the award
- `reject(reviewer, rejection_reason, comments)`: Reject the award

## Configuration

### Settings

Add to your Django settings:

```python
# Threshold for suspicious activity detection (awards per hour)
DIRECT_AWARD_THRESHOLD_PER_HOUR = 10

# Email addresses for admin notifications
ADMIN_NOTIFICATION_EMAILS = ['admin1@example.edu', 'admin2@example.edu']
```

## Management Commands

### Check Direct Award Thresholds

```bash
python manage.py check_direct_award_thresholds
```

This command:
1. Checks for suspicious direct award activity
2. Notifies admins about pending approvals
3. Can be scheduled to run periodically

## Workflow Examples

### Standard Workflow (No Approval Required)

1. Teacher creates direct award bundle with `requires_approval: false`
2. Awards are created with `STATUS_UNACCEPTED`
3. Students receive notifications immediately
4. Students can claim awards as before

### Approval Workflow

1. Teacher creates direct award bundle with `requires_approval: true`
2. Awards are created with `STATUS_PENDING_APPROVAL`
3. Admin reviews pending awards via `/pending-approvals` endpoint
4. Admin approves or rejects each award via `/approval/{entity_id}` endpoint
5. Teacher receives email notification with decision
6. If approved: award status changes to `STATUS_APPROVED`, student can claim
7. If rejected: award status changes to `STATUS_REJECTED`, no student notification

### Threshold Monitoring Workflow

1. System monitors direct award creation activity
2. When thresholds are exceeded, admins are notified
3. Admins can review suspicious activity and take action
4. Regular monitoring helps prevent abuse

## Migration Guide

### For Existing Implementations

The new approval workflow is completely optional and backward compatible:

1. **No changes required**: Existing code continues to work unchanged
2. **Opt-in approval**: Set `requires_approval: true` to use new workflow
3. **Gradual adoption**: Can be enabled per badgeclass or institution

### New Implementations

1. Decide which badgeclasses require approval
2. Set `requires_approval: true` when creating bundles for those badgeclasses
3. Train admins on the approval process
4. Configure threshold monitoring as needed

## Security Considerations

- **Permission Control**: Only users with `may_award` permission can approve/reject awards
- **Audit Trail**: All approval decisions are recorded with timestamps and user information
- **Rate Limiting**: Threshold monitoring helps prevent abuse
- **Data Protection**: Sensitive information is properly handled in notifications

## Troubleshooting

### Common Issues

**Issue**: Awards not showing in pending approvals
- **Solution**: Check that `requires_approval: true` was set during creation
- **Solution**: Verify user has permission to view approvals for the institution

**Issue**: Approval emails not being sent
- **Solution**: Check email configuration in Django settings
- **Solution**: Verify creator has a valid email address

**Issue**: Threshold monitoring not working
- **Solution**: Ensure `DIRECT_AWARD_THRESHOLD_PER_HOUR` is set in settings
- **Solution**: Check that the management command is scheduled to run

## Future Enhancements

Potential future improvements:
- **Bulk approval**: Approve/reject multiple awards at once
- **Delegation**: Allow delegation of approval authority
- **Escalation**: Automatic escalation for high-value awards
- **Analytics**: Dashboard showing approval metrics and trends
- **Integration**: Connect with institutional approval systems

## Support

For issues or questions about the direct award approval workflow:

- Check the API documentation for detailed endpoint specifications
- Review the management command help for threshold monitoring
- Consult the Django admin interface for approval record inspection
- Contact system administrators for permission-related issues