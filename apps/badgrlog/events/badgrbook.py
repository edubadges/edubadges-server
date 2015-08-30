# Created by wiggins@concentricsky.com on 8/27/15.
from .base import BaseBadgrEvent


class BaseBadgrLtiEvent(BaseBadgrEvent):
    def __init__(self, request):
        self.request = request

    def to_representation(self):
        LTI = self.request.session.get('LTI', None)
        if LTI is None or len(LTI) < 1:
            return {}
        return {
            'LTI': {
                'tool_consumer_instance_guid': LTI.get('tool_consumer_instance_guid', None),
                'tool_consumer_info_product_family_code': LTI.get('tool_consumer_info_product_family_code', None),
                'tool_consumer_instance_name': LTI.get('tool_consumer_instance_name', None),
                'course_id': LTI.get('custom_canvas_course_id', None),
                'course_name': LTI.get('context_title', LTI.get('context_label', None)),
                'user_email': LTI.get('lis_person_contact_email_primary', None),
                'user_id': LTI.get('user_id', None),
                'roles': LTI.get('roles', []),
            }
        }


class InstructorAssignedIssuerEvent(BaseBadgrLtiEvent):
    def __init__(self, request, serialized_issuer):
        super(InstructorAssignedIssuerEvent, self).__init__(request)
        self.issuer = serialized_issuer

    def to_representation(self):
        data = super(InstructorAssignedIssuerEvent, self).to_representation()
        data.update({
            'issuer': self.issuer.get('json').get('id'),
        })
        return data


class BadgeObjectiveCreatedEvent(BaseBadgrLtiEvent):
    def __init__(self, request, serialized_badge_objective):
        super(BadgeObjectiveCreatedEvent, self).__init__(request)
        self.badge_objective = serialized_badge_objective

    def to_representation(self):
        data = super(BadgeObjectiveCreatedEvent, self).to_representation()
        data.update({
            'badge_class': self.badge_objective.get('badge_class').get('json').get('id'),
            'objective_id': self.badge_objective.get('objective_id', None),
            'objective_type': self.badge_objective.get('objective_type', None),
            'objective_name': self.badge_objective.get('objective_name', None),
        })
        return data


class BadgeObjectiveUpdatedEvent(BadgeObjectiveCreatedEvent):
    pass


class BadgeObjectiveAwardedEvent(BaseBadgrEvent):
    def __init__(self, badge_award, serialized_badge_instance):
        self.badge_award = badge_award
        self.badge_instance = serialized_badge_instance

    def to_representation(self):
        return {
            'student_id': self.badge_award.student_id,
            'badge_instance': self.badge_instance.get('badge_instance').get('id'),
            'badge_class': self.badge_instance.get('badge_class'),
            'objective_id': self.badge_award.badge_objective.objective_id,
            'objective_type': self.badge_award.badge_objective.objective_type,

        }
