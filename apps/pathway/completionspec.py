# Created by wiggins@concentricsky.com on 4/1/16.
import json
from collections import OrderedDict

from django.core.urlresolvers import reverse


class CompletionRequirementSpec(object):
    def __init__(self, completion_type=None, junction_type=None, required_number=None):
        self.completion_type = completion_type
        self.junction_type = junction_type
        self.required_number = required_number

    def handle_json(self, json_obj):
        pass

    def serialize(self):
        obj = OrderedDict([
            ("@type", self.completion_type),
            ("junctionConfig", {"@type": self.junction_type, "requiredNumber": self.required_number}),
        ])
        return obj

    def check_completion(self, *args, **kwargs):
        raise NotImplementedError


class ElementJunctionCompletionRequirementSpec(CompletionRequirementSpec):
    def __init__(self, *args, **kwargs):
        self.elements = set(kwargs.pop('elements'))
        super(ElementJunctionCompletionRequirementSpec, self).__init__(*args, **kwargs)

    def serialize(self):
        obj = super(ElementJunctionCompletionRequirementSpec, self).serialize()
        obj.update([("elements", self.elements)])
        return obj

    def handle_json(self, json_obj):
        self.elements = set(json_obj.get('elements'))
        if not self.elements:
            raise ValueError("elements are required when @type is {}".format(self.completion_type))

    def check_completion(self, elements=()):
        raise NotImplementedError


class BadgeJunctionCompletionRequirementSpec(CompletionRequirementSpec):
    def __init__(self, *args, **kwargs):
        self.badges = set(kwargs.pop('badges'))
        super(BadgeJunctionCompletionRequirementSpec, self).__init__(*args, **kwargs)

    def serialize(self):
        obj = super(BadgeJunctionCompletionRequirementSpec, self).serialize()
        obj.update([("badges", self.badges)])
        return obj

    def handle_json(self, json_obj):
        self.badges = set(json_obj.get('badges'))
        if not self.badges:
            raise ValueError("badges are required when @type is {}".format(self.completion_type))

    def check_completion(self, instances=()):
        completion = {
            'completed': False,
        }
        if self.required_number < 1:
            return completion
        earned_count = len(instances)
        if earned_count < self.required_number:
            return completion

        all_earned_badges = set(reverse('badgeclass_json', kwargs={'slug': i.cached_badgeclass.slug}) for i in instances)
        required_earned_badges = self.badges & all_earned_badges
        completion['completedBadges'] = required_earned_badges

        if self.junction_type == CompletionRequirementSpecFactory.JUNCTION_TYPE_DISJUNCTION:
            if len(required_earned_badges) >= self.required_number:
                completion['completed'] = True
        elif self.junction_type == CompletionRequirementSpecFactory.JUNCTION_TYPE_JUNCTION:
            if self.badges <= required_earned_badges:  # every element in self.badges is in required_earned_badges
                completion['completed'] = True
        return completion


class CompletionRequirementSpecFactory(object):
    BADGE_JUNCTION = 'BadgeJunction'
    ELEMENT_JUNCTION = 'ElementJunction'
    COMPLETION_TYPES = {
        BADGE_JUNCTION: BadgeJunctionCompletionRequirementSpec,
        ELEMENT_JUNCTION: ElementJunctionCompletionRequirementSpec,
    }

    JUNCTION_TYPE_DISJUNCTION = 'Disjunction'
    JUNCTION_TYPE_JUNCTION = 'Junction'
    JUNCTION_TYPES = (JUNCTION_TYPE_DISJUNCTION, JUNCTION_TYPE_JUNCTION)

    @classmethod
    def parse(cls, json_str):
        json_obj = json.loads(json_str)

        completion_type = json_obj.get('@type')
        if completion_type not in cls.COMPLETION_TYPES.keys():
            raise ValueError("Invalid @type: {}".format(completion_type))

        junction_conf = json_obj.get('junctionConfig')
        if not junction_conf:
            raise ValueError("Invalid junctionConfig")

        junction_type = junction_conf.get("@type")
        if junction_type not in cls.JUNCTION_TYPES:
            raise ValueError("Invalid junctionConfig @type: {}".format(junction_type))

        required_number = junction_conf.get("requiredNumber")
        if not required_number:
            raise ValueError("Invalid junctionConfig missing requiredNumber")
        try:
            junction_required = int(required_number)
        except ValueError:
            raise ValueError("Invalid requiredNumber: {}".format(required_number))

        spec_cls = cls.COMPLETION_TYPES.get(completion_type)
        spec = spec_cls(completion_type=completion_type,
                        junction_type=junction_type,
                        required_number=junction_required)
        spec.handle_json(json_obj)
        return spec
