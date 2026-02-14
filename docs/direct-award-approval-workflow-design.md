# Direct Award Approval Workflow - Design Document

## Problem Statement

The current direct award system lacks oversight and abuse prevention mechanisms. Institution administrators need the ability to review and approve direct award requests before they are sent to recipients to ensure appropriate use of the direct awarding system and prevent potential abuse.

## Glossary

- **Direct Award**: A badge awarded directly to a recipient without requiring them to complete specific criteria
- **EPPN**: EduPersonPrincipalName - a unique identifier for users in the education system
- **BadgeClass**: The template or definition of a badge that can be awarded
- **Institution Admin**: User with administrative privileges for an educational institution
- **Threshold Monitoring**: System that detects suspicious activity patterns based on configurable limits

## Use Cases

### 1. Prevent Abuse of Direct Awards
**Impact**: Reduce inappropriate badge awards and maintain system integrity
**Example**: A teacher attempts to award 50 badges to the same student in one day. The system flags this for admin review before awards are sent.

### 2. Quality Control for High-Value Badges
**Impact**: Ensure prestigious badges maintain their value and credibility
**Example**: An institution wants all "Dean's List" badges to be reviewed by an administrator before being awarded to students.

### 3. Compliance with Institutional Policies
**Impact**: Meet institutional requirements for badge awarding processes
**Example**: A university policy requires all academic achievement badges to be approved by the registrar's office.

### 4. Detection of Suspicious Activity
**Impact**: Proactively identify and prevent potential system abuse
**Example**: The system detects that a single teacher is creating 100 direct awards per hour and alerts administrators.

## Breaking Changes

### API Changes
- New required field `requires_approval` in direct award bundle creation (defaults to `false` for backward compatibility)
- New status values for DirectAward model: `STATUS_PENDING_APPROVAL`, `STATUS_APPROVED`, `STATUS_REJECTED`

### Database Changes
- New `DirectAwardApproval` model with foreign key relationship to `DirectAward`
- Additional fields added to existing `DirectAward` model for approval tracking

### Workflow Changes
- Direct awards with `requires_approval=true` will not be immediately available to recipients
- Recipients will not receive notifications for awards until they are approved
- Teachers will receive notifications about approval decisions

## Success Criteria

### Quantitative Metrics
- **Adoption Rate**: 75% of institutions enable approval workflow within 6 months of release
- **Abuse Reduction**: 90% reduction in reported inappropriate direct awards within 12 months
- **Review Time**: 95% of approval requests processed within 48 hours
- **System Performance**: Approval workflow adds <500ms to direct award creation time

### Qualitative Metrics
- **User Satisfaction**: Positive feedback from institution administrators about oversight capabilities
- **Policy Compliance**: Institutions can demonstrate compliance with internal badge awarding policies
- **Abuse Prevention**: Reduced incidents of badge system misuse reported by institutions

## Proposed Design

The direct award approval workflow introduces a security-focused process for award creation and monitoring:

1. **Default Pending State**: All direct awards are created in `STATUS_PENDING_APPROVAL` state by default
2. **Real-time Threshold Monitoring**: System actively checks each incoming direct award request against configurable thresholds
3. **Automatic Approval**: Awards that pass threshold checks are automatically approved and become available
4. **Admin Review for Suspicious Activity**: Awards flagged by threshold monitoring require admin review
5. **Notification System**: Automated notifications for approvals, rejections, and review requests

## Technical Design

### Architecture Overview

```
[Teacher] → [Direct Award API] → [DirectAward Model]
                             ↓
                  [DirectAwardApproval Model]
                             ↓
[Admin Review Interface] ← [Approval API]
                             ↓
[Notification Service] → [Email System]
                             ↓
[Threshold Monitor] → [Alert System]
```

### Key Components

#### 1. DirectAward Model Enhancements
- Added status constants: `STATUS_PENDING_APPROVAL`, `STATUS_APPROVED`, `STATUS_REJECTED`, `STATUS_BLOCKED`
- Added methods: `automatic_approval_check()`, `flag_for_review()`, `approve()`, `reject()`
- Modified creation workflow to default to pending approval state

#### 2. DirectAwardApproval Model
- One-to-one relationship with DirectAward
- Tracks approval status, reviewer, timestamps, and comments
- Stores rejection reasons and threshold violation details

#### 3. Real-time Threshold Monitoring
- Active checking of each direct award request
- Configurable thresholds (per user, per institution, time-based)
- Immediate blocking of suspicious requests
- Admin notification system for flagged awards

#### 4. Approval API Endpoints
- `GET /directaward/pending-approvals` - List awards needing admin review
- `POST /directaward/approval/{entity_id}` - Admin approve or reject flagged awards
- Enhanced bundle creation with automatic threshold checking

### Data Flow

1. Teacher creates direct award bundle request
2. System creates DirectAward record with `STATUS_PENDING_APPROVAL`
3. Real-time threshold monitor checks the request against configurable rules
4. If thresholds passed: System automatically approves award (`STATUS_APPROVED`)
5. If thresholds violated: Award flagged as `STATUS_BLOCKED` and requires admin review
6. Admin reviews blocked awards and makes final decision
7. System sends appropriate notifications throughout the process

## Components

- **Direct Award API**: Handles creation and management of direct awards with built-in threshold checking
- **Real-time Monitoring Service**: Actively checks each request against configurable thresholds
- **Approval System**: Manages admin review process for flagged awards
- **Notification Service**: Sends email alerts for approvals, rejections, and review requests
- **Database**: Stores award and approval records with detailed audit trail
- **Admin Interface**: Web interface for reviewing blocked awards

## Dependencies

- Django REST Framework for API endpoints
- Django Signals for notification triggers
- Celery for asynchronous notification delivery
- Institution and User models for permission checking
- Email service for notification delivery

## Monitoring

### Technical Metrics
- **API Response Time**: Track response times for direct award creation with threshold checking
- **Threshold Check Performance**: Monitor real-time monitoring system latency
- **Database Performance**: Query performance for approval and blocking operations
- **Notification Delivery**: Success/failure rates for all notification types
- **False Positive Rate**: Percentage of legitimate awards incorrectly blocked

### Business Metrics
- **Auto-Approval Rate**: Percentage of awards automatically approved by system
- **Admin Review Volume**: Number of awards requiring manual review
- **Block Rate**: Percentage of awards blocked by threshold monitoring
- **Processing Time**: Average time from creation to final status (approved/available)

## New APIs or Behaviors

### Public-Facing API Changes

1. **Bundle Creation with Automatic Monitoring**
   - All direct awards now go through threshold monitoring by default
   - Removed `requires_approval` field (system determines need for review)
   - Added `threshold_check_results` to response showing monitoring decision

2. **Blocked Awards Endpoint**
   - New GET endpoint for listing awards blocked by threshold monitoring
   - Filterable by institution, user, and block reason
   - Returns detailed award information and threshold violation details

3. **Admin Override Endpoint**
   - New POST endpoint for admin to override threshold decisions
   - Supports both approve (override block) and reject (confirm block) actions
   - Requires admin comments explaining override decision

### Internal Behavior Changes

- All direct awards now go through real-time threshold monitoring
- Awards are blocked immediately if thresholds are violated
- System generates different notifications based on monitoring outcome:
  - Auto-approval notifications for clean awards
  - Admin review notifications for blocked awards
- Threshold monitoring integrated directly into award creation workflow

## Pros & Cons

### Pros
- **Proactive Abuse Prevention**: Real-time blocking of suspicious awards before they're sent
- **Automated Processing**: Most legitimate awards approved automatically without admin intervention
- **Focused Admin Review**: Admins only review truly suspicious cases, not all awards
- **Comprehensive Security**: Default-deny approach with explicit approval requirements
- **Complete Audit Trail**: Full record of all monitoring decisions and admin actions

### Cons
- **Potential Delays**: Legitimate awards may be blocked requiring admin review
- **False Positives**: Legitimate high-volume awards might be incorrectly blocked
- **System Complexity**: Real-time monitoring adds complexity to award creation
- **Performance Impact**: Additional processing during award creation
- **Configuration Overhead**: Institutions need to configure appropriate thresholds

## Major Risks & Mitigations

### Risk: High False Positive Rate
**Mitigation**:
- Implement configurable thresholds per institution
- Provide admin override capabilities for blocked awards
- Monitor and adjust threshold algorithms based on real-world data
- Implement machine learning to improve detection accuracy over time

### Risk: Performance Impact on Award Creation
**Mitigation**:
- Optimize threshold checking algorithms for speed
- Implement caching for user/institution award history
- Use asynchronous processing where possible
- Monitor and tune performance continuously

### Risk: Legitimate Awards Being Blocked
**Mitigation**:
- Implement clear admin notification system for blocked awards
- Provide easy admin override process
- Track and analyze false positives to improve algorithms
- Offer emergency bypass procedures for critical awards

### Risk: Threshold Configuration Complexity
**Mitigation**:
- Provide sensible default thresholds
- Offer threshold configuration wizards
- Provide examples and best practices documentation
- Implement threshold validation to prevent misconfiguration

## Security

### Data Protection
- Monitoring decisions and admin actions contain sensitive information
- Ensure proper access controls for all monitoring and approval data
- Encrypt sensitive threshold violation details
- Audit logging for all monitoring decisions and admin actions

### Permission Control
- Only users with `may_award` permission can override threshold blocks
- Institution-level permission checking for all admin review operations
- Prevent privilege escalation through monitoring system bypass
- Implement separation of duties for threshold configuration

### Audit Trail
- All monitoring decisions recorded with timestamps and criteria
- All admin override actions stored with detailed reasoning
- Complete history of threshold changes and configurations
- Immutable logs for compliance and forensic analysis

## Scope

### In Scope
- Real-time threshold monitoring system
- API integration for automatic award checking
- Database models for tracking monitoring decisions
- Admin review interface for blocked awards
- Comprehensive notification system
- Threshold configuration management

### Minimum Viable Product
- Real-time threshold checking on award creation
- Basic threshold rules (count per time period)
- Admin override capability
- Basic notifications for blocked awards
- Simple threshold configuration interface

## Out of Scope

### Future Enhancements
- Machine learning for improved threshold detection
- Advanced threshold rules (behavioral patterns, anomaly detection)
- Integration with institutional SIEM systems
- Comprehensive security analytics dashboard
- Automated threshold tuning based on historical data

### Not Included in Initial Release
- Mobile interface for admin overrides
- Advanced reporting and visualization
- Multi-factor threshold systems
- Automated remediation workflows

## Alternatives Considered

### Alternative #1: Optional Threshold Monitoring
**Description**: Make threshold monitoring optional rather than default

**Pros**: Less impact on existing workflows, gradual adoption possible

**Cons**: Reduced security posture, inconsistent protection across institutions

**Reasons Discarded**: Does not meet security requirements, leaves system vulnerable

### Alternative #2: Post-Creation Batch Monitoring
**Description**: Run threshold monitoring as batch process after award creation

**Pros**: No impact on award creation performance, simpler implementation

**Cons**: Cannot prevent abusive awards from being sent, only react after the fact

**Reasons Discarded**: Does not meet proactive security requirements

### Alternative #3: User Reputation System
**Description**: Implement reputation system where trusted users bypass monitoring

**Pros**: Reduces false positives for trusted users, improves user experience

**Cons**: Complex to implement, reputation gaming possible, security risks

**Reasons Discarded**: Too complex for initial implementation, security concerns

## Open Questions & Feedback

- What should be the default threshold values for different institution sizes?
- How should we handle awards that are blocked but the admin is unavailable?
- Should we implement emergency bypass procedures for critical awards?
- How detailed should threshold violation explanations be in notifications?
- Should we provide API endpoints for programmatic threshold overrides?

## Appendix

### Database Schema Changes

```sql
-- New table for monitoring and approval tracking
CREATE TABLE directaward_directawardmonitoring (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    direct_award_id INTEGER NOT NULL UNIQUE,
    monitoring_status VARCHAR(20) NOT NULL,
    threshold_violations JSON,
    auto_approved BOOLEAN DEFAULT FALSE,
    reviewed_by_id INTEGER,
    review_date DATETIME,
    admin_comments TEXT,
    block_reason TEXT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (direct_award_id) REFERENCES directaward_directaward(id),
    FOREIGN KEY (reviewed_by_id) REFERENCES auth_user(id)
);

-- Modified DirectAward table
ALTER TABLE directaward_directaward 
ADD COLUMN monitoring_status VARCHAR(20) DEFAULT 'pending';

-- New table for threshold configuration
CREATE TABLE directaward_thresholdconfiguration (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    institution_id INTEGER,
    threshold_type VARCHAR(50) NOT NULL,
    threshold_value INTEGER NOT NULL,
    time_window_minutes INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (institution_id) REFERENCES institution_institution(id)
);
```

### Configuration Example

```python
# settings.py
DIRECT_AWARD_MONITORING = {
    'DEFAULT_THRESHOLDS': {
        'MAX_PER_HOUR': 10,
        'MAX_PER_DAY': 50,
        'MAX_SAME_RECIPIENT': 3,
        'MAX_SAME_BADGECLASS': 5
    },
    'MONITORING_TIMEOUT': 5000,  # milliseconds
    'ADMIN_NOTIFICATION_EMAILS': ['admin1@example.edu', 'admin2@example.edu'],
    'NOTIFICATION_TEMPLATES': {
        'AUTO_APPROVED': 'direct_award_auto_approved.html',
        'BLOCKED': 'direct_award_blocked.html',
        'ADMIN_OVERRIDE': 'direct_award_admin_override.html'
    },
    'ENABLE_THRESHOLD_LEARNING': False  # Future enhancement
}
```

### Example Workflow Timeline

```
Day 1:
- 09:00: Teacher creates 3 direct awards (normal volume)
- 09:00: System performs real-time threshold check
- 09:00: All awards pass checks, auto-approved immediately
- 09:00: Students receive award notifications
- 09:01: System logs monitoring decisions

- 14:00: Teacher attempts to create 15 awards in one hour
- 14:00: System performs real-time threshold check
- 14:00: Threshold violation detected (MAX_PER_HOUR: 10)
- 14:00: Awards blocked with STATUS_BLOCKED
- 14:00: Admin receives blocked award notification
- 14:15: Admin reviews and overrides block for legitimate awards
- 14:16: Overridden awards become available to students
- 14:16: System logs admin override with reasoning

Day 2:
- 10:00: Teacher creates award for same student 4th time today
- 10:00: System detects MAX_SAME_RECIPIENT violation
- 10:00: Award blocked and flagged for admin review
- 10:05: Admin confirms block due to suspicious pattern
- 10:05: Teacher receives notification about blocked award
```

### Performance Considerations

- Optimized threshold checking algorithms for real-time performance
- Caching of user award history to speed up threshold calculations
- Database indexing for monitoring status and block reasons
- Asynchronous notification delivery to avoid blocking award creation
- Connection pooling for database operations during monitoring

### Migration Strategy

1. Deploy new code with feature flags disabled
2. Run database migrations to add new tables/columns
3. Enable feature flags for pilot institutions
4. Monitor system performance and user feedback
5. Gradual rollout to all institutions
6. Deprecate old workflow after full adoption

### Testing Approach

- Unit tests for threshold checking algorithms
- Integration tests for real-time monitoring during award creation
- Performance tests for monitoring system under load
- Security testing for threshold bypass attempts
- User acceptance testing with admin override workflow
- Load testing with high-volume award creation scenarios
- False positive/negative rate analysis
