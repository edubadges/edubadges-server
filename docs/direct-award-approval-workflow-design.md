# Direct Award Approval Workflow - Design Document

## Problem Statement

The current direct award system lacks oversight and abuse prevention mechanisms. Institution administrators need the ability to review and approve direct award requests, in case threshold limits are reached, before they are sent to recipients. This approval step ensures appropriate use of the direct awarding system and prevents potential abuse.

## Key Terms

- **Direct Award**: A badge awarded directly to a recipient without requiring them to request the award
- **EPPN**: EduPersonPrincipalName - a unique identifier for users in the education system
- **BadgeClass**: The template or definition of a badge that can be awarded
- **Institution Admin**: User with administrative privileges for an educational institution
- **Awarder**: User with awarding privileges to create direct awards
- **Threshold Monitoring**: System that detects suspicious activity patterns based on configurable limits

## Use Cases

The system needs to prevent abuse of direct awards, ensure quality control for high-value badges, comply with institutional policies, and detect suspicious activity. For instance, an awarder attempting to award more than 1000 badges in one day should be flagged for admin review before awards are sent.

## Breaking Changes

The API changes include a new required field `requires_approval` in direct award bundle creation that defaults to `false` for backward compatibility. New status values for DirectAward model include `STATUS_PENDING_APPROVAL`, `STATUS_APPROVED`, and `STATUS_REJECTED`. Database changes involve a new `DirectAwardApproval` model with foreign key relationship to `DirectAward` and additional fields added to existing `DirectAward` model for approval tracking. Workflow changes mean that direct awards with `requires_approval=true` will not be immediately available to recipients, recipients will not receive notifications for awards until they are approved, and teachers will receive notifications about approval decisions.

## Success Criteria

Qualitative metrics involve positive feedback from institution administrators about oversight capabilities, institutions being able to demonstrate compliance with internal credential awarding policies, and reduced incidents of badge system misuse reported by institutions. Quantitative metrics do not apply.

## Proposed Design

The direct award approval workflow introduces a security-focused process for award creation and monitoring. All direct awards are created in `STATUS_PENDING_APPROVAL` state by default. The system actively checks each incoming direct award request against configurable thresholds. Awards that pass threshold checks are automatically approved and become available. Awards flagged by threshold monitoring require admin review. Automated notifications are sent for approvals, rejections, and review requests.

## Technical Design

### Architecture Overview

The architecture involves an awarder creating a direct award request that goes through the Direct Award API to the DirectAward Model. The DirectAwardApproval Model then processes the request, which can be reviewed by an admin through the Admin Review Interface. The Approval API handles the approval or rejection of the request, and the Notification Service sends email alerts. The Threshold Monitor detects suspicious activity and sends alerts.

### Key Components

DirectAward Model Enhancements include added status constants such as `STATUS_PENDING_APPROVAL`, `STATUS_APPROVED`, `STATUS_REJECTED`, and `STATUS_BLOCKED`. Added methods include `automatic_approval_check()`, `flag_for_review()`, `approve()`, and `reject()`. The creation workflow has been modified to default to pending approval state.

The DirectAwardApproval Model has a one-to-one relationship with DirectAward, tracks approval status, reviewer, timestamps, and comments, and stores rejection reasons and threshold violation details.

Real-time Threshold Monitoring involves active checking of each direct award request, configurable thresholds (per user, per institution, time-based), immediate blocking of suspicious requests, and an admin notification system for flagged awards.

Approval API Endpoints include `GET /directaward/pending-approvals` to list awards needing admin review, `POST /directaward/approval/{entity_id}` for admin to approve or reject flagged awards, and enhanced bundle creation with automatic threshold checking.

### Data Flow

The data flow starts with an awarder creating a direct award bundle request. The system creates a DirectAward record with `STATUS_PENDING_APPROVAL`. The real-time threshold monitor then checks the request against configurable rules. If thresholds are passed, the system automatically approves the award with `STATUS_APPROVED`. If thresholds are violated, the award is flagged as `STATUS_BLOCKED` and requires admin review. The admin reviews blocked awards and makes a final decision. The system sends appropriate notifications throughout the process via email to either the awarder or institution admin.

## Components

The components that needs to be created or updated include the Direct Award API that handles creation and management of direct awards with built-in threshold checking, the Real-time Monitoring Service that actively checks each request against configurable thresholds, the Approval System that manages the admin review process for flagged awards, the Notification Service that sends email alerts for approvals, rejections, and review requests, the Database that stores award and approval records with detailed audit trail, and the Institution Admin Interface that provides a web interface for reviewing blocked awards.

## Dependencies

- Django REST Framework for API endpoints
- Django Signals for notification triggers
- Celery for asynchronous notification delivery
- Institution and User models for permission checking
- Email service for notification delivery

## Monitoring

Technical metrics to monitor include API response time for direct award creation with threshold checking, threshold check performance, database performance for approval and blocking operations, notification delivery success/failure rates, and false positive rate of legitimate awards incorrectly blocked. Business metrics include auto-approval rate, admin review volume, block rate, and processing time from creation to final status.

## Pros & Cons

Pros of the system include proactive abuse prevention through real-time blocking of suspicious awards before they're sent, automated processing where most legitimate awards are approved automatically without admin intervention, focused admin review where admins only review truly suspicious cases, comprehensive security with a default-deny approach and explicit approval requirements, and a complete audit trail with a full record of all monitoring decisions and admin actions.

Cons include potential delays where legitimate awards may be blocked requiring admin review, false positives where legitimate high-volume awards might be incorrectly blocked, system complexity where real-time monitoring adds complexity to award creation, performance impact with additional processing during award creation, and configuration overhead where institutions need to configure appropriate thresholds.

## Major Risks & Mitigations

The risk of high false positive rate can be mitigated by implementing configurable thresholds per institution, providing admin override capabilities for blocked awards, monitoring and adjusting threshold algorithms based on real-world data, and implementing machine learning to improve detection accuracy over time.

Performance impact on award creation can be mitigated by optimizing threshold checking algorithms for speed, implementing caching for user/institution award history, using asynchronous processing where possible, and monitoring and tuning performance continuously.

The risk of legitimate awards being blocked can be mitigated by implementing a clear admin notification system for blocked awards, providing an easy admin override process, tracking and analyzing false positives to improve algorithms, and offering emergency bypass procedures for critical awards.

Threshold configuration complexity can be mitigated by providing sensible default thresholds, offering threshold configuration wizards, providing examples and best practices documentation, and implementing threshold validation to prevent misconfiguration.

## Security

Data protection measures include ensuring that monitoring decisions and admin actions contain sensitive information, proper access controls for all monitoring and approval data, encryption of sensitive threshold violation details, and audit logging for all monitoring decisions and admin actions.

Permission control involves only instituion admins being able to override threshold blocks, institution-level permission checking for all admin review operations, and implementation of separation of duties for threshold configuration.

Audit trail measures include recording all monitoring decisions with timestamps and criteria, storing all admin override actions with detailed reasoning, maintaining a complete history of threshold changes and configurations, and keeping immutable logs for compliance and forensic analysis.

## Scope

The scope includes a real-time threshold monitoring system, API integration for automatic award checking, database models for tracking monitoring decisions, an admin review interface for blocked awards, a comprehensive notification system, and threshold configuration management.

The minimum viable product includes real-time threshold checking on award creation, basic threshold rules (count per time period), admin override capability, basic notifications for blocked awards, and a simple threshold configuration interface.

## Out of Scope

Future enhancements include machine learning for improved threshold detection, advanced threshold rules (behavioral patterns, anomaly detection), integration with institutional SIEM systems, and automated threshold tuning based on historical data.

Not included in the initial release are advanced reporting and visualization, multi-factor threshold systems, and automated remediation workflows.

## Alternatives Considered

Alternative #1: Optional Threshold Monitoring would make threshold monitoring optional rather than default. Pros include less impact on existing workflows and gradual adoption being possible. Cons include reduced security posture and inconsistent protection across institutions. This alternative was discarded because it does not meet security requirements and leaves the system vulnerable.

Alternative #2: Post-Creation Batch Monitoring would run threshold monitoring as a batch process after award creation. Pros include no impact on award creation performance and simpler implementation. Cons include the inability to prevent abusive awards from being sent and only being able to react after the fact. This alternative was discarded because it does not meet proactive security requirements.

Alternative #3: User Reputation System would implement a reputation system where trusted users bypass monitoring. Pros include reduced false positives for trusted users and improved user experience. Cons include complexity to implement, reputation gaming being possible, and security risks. This alternative was discarded because it is too complex for initial implementation and has security concerns.

## Open Questions & Feedback

- What should be the default threshold values for different institution sizes?
- How should we handle awards that are blocked but the admin is unavailable?
- Should we implement emergency bypass procedures for critical awards?
- How detailed should threshold violation explanations be in notifications?
- Should we provide API endpoints for programmatic threshold overrides?

## Appendix

### Database Schema Changes

Database schema changes include a new table for monitoring and approval tracking with fields for monitoring status, threshold violations, auto-approved status, reviewed by, review date, admin comments, block reason, and timestamps. The DirectAward table is modified to add a monitoring_status column. A new table for threshold configuration is added with fields for institution ID, threshold type, threshold value, time window, active status, and timestamps.

### Configuration Example

The configuration example shows how to set up default thresholds for maximum awards per hour and day, maximum same recipient awards, and maximum same badgeclass awards. It also includes settings for monitoring timeout, admin notification emails, notification templates for different scenarios, and a flag for enabling threshold learning as a future enhancement.

### Example Workflow Timeline

The example workflow timeline demonstrates how the system handles normal volume awards that pass threshold checks and are auto-approved immediately, versus high-volume awards that trigger threshold violations and require admin review and override. It also shows how the system handles awards to the same recipient multiple times in a day, flagging them for admin review.

### Performance Considerations

Performance considerations include optimized threshold checking algorithms for real-time performance, caching of user award history to speed up threshold calculations, database indexing for monitoring status and block reasons, asynchronous notification delivery to avoid blocking award creation, and connection pooling for database operations during monitoring.

### Migration Strategy

The migration strategy involves deploying new code with feature flags disabled, running database migrations to add new tables/columns, enabling feature flags for pilot institutions, monitoring system performance and user feedback, gradual rollout to all institutions, and deprecating the old workflow after full adoption.

### Testing Approach

The testing approach includes unit tests for threshold checking algorithms, integration tests for real-time monitoring during award creation, performance tests for monitoring system under load, security testing for threshold bypass attempts, user acceptance testing with admin override workflow, load testing with high-volume award creation scenarios, and false positive/negative rate analysis.

### Django 5 Best Practices Analysis

The implementation has been reviewed for Django 5 best practices compliance:

#### ✅ Good Practices Applied:

1. **Model Inheritance**: Proper use of Django's abstract base classes (`BaseAuditedModel`, `BaseVersionedEntity`, `CacheModel`)
2. **Field Types**: Appropriate use of Django field types (EmailField, CharField, TextField, IntegerField, DateTimeField, JSONField)
3. **Relationships**: Correct use of ForeignKey with proper on_delete behavior
4. **Model Methods**: Well-organized business logic in model methods
5. **Status Management**: Use of status constants with choices for better data integrity
6. **Error Handling**: Custom exceptions and proper validation

#### 🔄 Django 5 Specific Considerations:

1. **`models.JSONField`**: The code uses JSONField which is now built-in and optimized in Django 5
2. **Model Inheritance**: The multiple inheritance pattern is compatible with Django 5
3. **Query Optimization**: The code could benefit from Django 5's new query optimization features

#### 📋 Recommendations for Improvement:

1. **Use Django 5's `models.TextChoices`**:
   ```python
   # Instead of:
   STATUS_CHOICES = (
       (STATUS_UNACCEPTED, 'Unaccepted'),
       # ...
   )

   # Consider:
   class Status(models.TextChoices):
       UNACCEPTED = 'Unaccepted', 'Unaccepted'
       REVOKED = 'Revoked', 'Revoked'
       # ...
   ```

2. **Leverage Django 5's `Deferrable` for unique constraints** where applicable
3. **Consider using Django 5's `Index` improvements** for better database performance
4. **Use `models.CheckConstraint`** for additional data validation at database level
5. **Implement Django 5's `Prefetch` optimizations** for related object queries

#### 🎯 API and Serialization:

The API implementation follows RESTful principles and uses DRF effectively. For Django 5, consider:
1. **Using Django 5's improved `json` module** for JSON serialization
2. **Leveraging Django 5's ASGI improvements** if using async views
3. **Considering Django 5's caching improvements** for better performance

#### 🔒 Security:

The implementation has good security practices with proper permission checking, input validation, secure error handling, and audit logging. For Django 5, ensure all security middleware is properly configured, CSRF protection is in place, and secure headers are set appropriately.

#### 🚀 Performance:

The code could benefit from Django 5's database connection pooling, improved caching strategies using Django 5's enhancements, and query optimization with Django 5's new features.

Overall, the implementation follows good Django practices and is compatible with Django 5. The recommendations above would further align the codebase with Django 5's latest features and best practices.
