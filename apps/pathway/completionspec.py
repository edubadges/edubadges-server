# Created by wiggins@concentricsky.com on 4/1/16.
import json
from collections import OrderedDict

from django.conf import settings
from django.urls import reverse

from pathway.models import PathwayElement


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
        self.elements = set(kwargs.pop('elements', []))
        super(ElementJunctionCompletionRequirementSpec, self).__init__(
            *args,
            completion_type=kwargs.pop('completion_type', CompletionRequirementSpecFactory.ELEMENT_JUNCTION),
            **kwargs)

    def serialize(self):
        obj = super(ElementJunctionCompletionRequirementSpec, self).serialize()
        obj.update([("elements", list(self.elements))])
        return obj

    def handle_json(self, json_obj):
        self.elements = set(json_obj.get('elements'))

    def check_completion(self, completion, completions, req_number=None):
        completion.update({
            'completedElements': [],
            'completedRequirementCount': 0
        })

        for element_id in self.elements:
            for completion_report in completions:
                if element_id == completion_report['element']['@id'] and completion_report['completed']:
                    # not using PathwayElement.cached.get_by_slug_or_id to lookup the slug here to improve performance
                    completion['completedElements'].append({'@id': element_id})
                    completion['completedRequirementCount'] += 1

        if completion['completedRequirementCount'] >= self.required_number:
            completion['completed'] = True

        return completion

    def check_completions(self, tree, instances):
        completions = []

        def _completion_base(node):
            completion = {
                "element": {
                    '@id': node['element'].jsonld_id,
                    'slug': node['element'].slug,
                },
                "completed": False,
            }
            if node['element'].completion_badgeclass:
                completion['completionBadge'] = {
                    '@id': node['element'].completion_badgeclass.jsonld_id,
                    'slug': node['element'].completion_badgeclass.entity_id,
                }
            return completion


        def _recurse(node):
            node_completion = _completion_base(node)

            if node['element'].completion_requirements:
                completion_spec = CompletionRequirementSpecFactory.parse_obj(
                    node['element'].completion_requirements
                )

                if completion_spec.completion_type == CompletionRequirementSpecFactory.ELEMENT_JUNCTION:
                    for element_id in completion_spec.elements:
                        child = node['children'].get(element_id, None)
                        if child:
                            _recurse(child)
                    # check optional children
                    for element_id in set(node['children'].keys()) - set(completion_spec.elements):
                        child = node['children'].get(element_id, None)
                        if child:
                            _recurse(child)
                    node_completion.update(completion_spec.check_completion(node_completion, completions))
                elif completion_spec.completion_type == CompletionRequirementSpecFactory.BADGE_JUNCTION:
                    node_completion.update(completion_spec.check_completion(node_completion, instances))
            completions.append(node_completion)
        _recurse(tree)

        return completions


class BadgeJunctionCompletionRequirementSpec(CompletionRequirementSpec):
    def __init__(self, *args, **kwargs):
        self.badges = set(kwargs.pop('badges', []))
        super(BadgeJunctionCompletionRequirementSpec, self).__init__(
            *args,
            completion_type=kwargs.pop('completion_type', CompletionRequirementSpecFactory.BADGE_JUNCTION),
            **kwargs)

    def serialize(self):
        obj = super(BadgeJunctionCompletionRequirementSpec, self).serialize()
        obj.update([("badges", list(self.badges))])
        return obj

    def handle_json(self, json_obj):
        self.badges = set(json_obj.get('badges'))

    def check_completion(self, completion, instances=()):
        completion['completedBadges'] = []
        for i in instances:
            if i.cached_badgeclass.json['id'] in self.badges:
                completion['completedBadges'].append({
                    '@id': i.cached_badgeclass.jsonld_id,
                    'slug': i.cached_badgeclass.entity_id,
                    'assertion': i.jsonld_id,
                })
        completion['completedRequirementCount'] = len(completion['completedBadges'])

        if self.junction_type == CompletionRequirementSpecFactory.JUNCTION_TYPE_DISJUNCTION:
            if completion['completedRequirementCount'] >= self.required_number:
                completion['completed'] = True
        elif self.junction_type == CompletionRequirementSpecFactory.JUNCTION_TYPE_CONJUNCTION:
            # every element in self.badges is in required_earned_badges
            if self.badges <= set([badge.get('@id') for badge in completion['completedBadges']]):
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
    JUNCTION_TYPE_CONJUNCTION = 'Conjunction'
    JUNCTION_TYPES = (JUNCTION_TYPE_DISJUNCTION, JUNCTION_TYPE_CONJUNCTION)

    @classmethod
    def parse(cls, json_str):
        try:
            cls.parse_obj(json.loads(json_str))
        except TypeError:
            return cls.parse_obj(json_str)

    @classmethod
    def parse_element(cls, element):
        if element.completion_requirements:
            return cls.parse_obj(element.completion_requirements)

    @classmethod
    def parse_obj(cls, json_obj):
        completion_type = json_obj.get('@type')
        if completion_type not in list(cls.COMPLETION_TYPES.keys()):
            raise ValueError("Invalid @type: {}".format(completion_type))

        junction_conf = json_obj.get('junctionConfig')
        if not junction_conf:
            raise ValueError("Invalid junctionConfig")

        junction_type = junction_conf.get("@type")
        if junction_type not in cls.JUNCTION_TYPES:
            raise ValueError("Invalid junctionConfig @type: {}".format(junction_type))

        required_number = junction_conf.get("requiredNumber")
        if junction_type == cls.JUNCTION_TYPE_DISJUNCTION:
            if not required_number:
                raise ValueError("Invalid junctionConfig missing requiredNumber")
            try:
                junction_required = int(required_number)
            except ValueError:
                raise ValueError("Invalid requiredNumber: {}".format(required_number))
        elif completion_type == cls.ELEMENT_JUNCTION:
            junction_required = len(json_obj['elements'])
        else:
            junction_required = len(json_obj['badges'])

        spec_cls = cls.COMPLETION_TYPES.get(completion_type)
        spec = spec_cls(completion_type=completion_type,
                        junction_type=junction_type,
                        required_number=junction_required)
        spec.handle_json(json_obj)
        return spec
