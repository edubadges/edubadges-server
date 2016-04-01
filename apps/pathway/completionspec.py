# Created by wiggins@concentricsky.com on 4/1/16.
import json
from collections import OrderedDict


class CompletionRequirementSpec(object):
    BADGE_JUNCTION = 'BadgeJunction'
    ELEMENT_JUNCTION = 'ElementJunction'
    COMPLETION_TYPES = (BADGE_JUNCTION, ELEMENT_JUNCTION)

    JUNCTION_TYPE_DISJUNCTION = 'Disjunction'
    JUNCTION_TYPE_JUNCTION = 'Junction'
    JUNCTION_TYPES = (JUNCTION_TYPE_DISJUNCTION, JUNCTION_TYPE_JUNCTION)

    def __init__(self, completion_type=None, junction_type=None, required_number=None, badges=(), elements=()):
        self.completion_type = completion_type
        self.junction_type = junction_type
        self.required_number = required_number
        self.badges = list(badges)
        self.elements = list(elements)

    @classmethod
    def parse(cls, json_str):
        json_obj = json.loads(json_str)

        completion_type = json_obj.get('@type')
        if completion_type not in cls.COMPLETION_TYPES:
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

        spec = CompletionRequirementSpec(completion_type=completion_type,
                                         junction_type=junction_type,
                                         required_number=junction_required)

        if completion_type == cls.BADGE_JUNCTION:
            spec.badges = json_obj.get('badges')
            if not spec.badges:
                raise ValueError("Could not find badges when @type is {}".format(cls.BADGE_JUNCTION))

        if completion_type == cls.ELEMENT_JUNCTION:
            spec.elements = json_obj.get('elements')
            if not spec.elements:
                raise ValueError("Could not find elements when @type is {}".format(cls.ELEMENT_JUNCTION))

        return spec

    def serialize(self):
        obj = OrderedDict([
            ("@type", self.completion_type),
            ("junctionConfig", {"@type": self.junction_type, "requiredNumber": self.required_number}),
        ])
        if self.completion_type == CompletionRequirementSpec.BADGE_JUNCTION:
            obj.update([("badges", self.badges)])
        if self.completion_type == CompletionRequirementSpec.ELEMENT_JUNCTION:
            obj.update([("elements", self.elements)])
        return obj





