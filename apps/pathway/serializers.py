# Created by wiggins@concentricsky.com on 3/30/16.
from collections import OrderedDict

from django.conf import settings
from django.core.urlresolvers import reverse, resolve, Resolver404
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from issuer.models import Issuer, BadgeClass
from mainsite.serializers import LinkedDataReferenceField, LinkedDataEntitySerializer
from pathway.completionspec import CompletionRequirementSpecFactory
from pathway.models import Pathway, PathwayElement
from recipient.models import RecipientGroup


class PathwayListSerializer(serializers.Serializer):

    def to_representation(self, pathways):
        pathways_serializer = PathwaySerializer(pathways, many=True, context=self.context)
        return OrderedDict([
            ("@context", "https://badgr.io/public/contexts/pathways"),
            ("@type", "IssuerPathwayList"),
            ("pathways", pathways_serializer.data),
        ])


class PathwaySerializer(serializers.Serializer):
    slug = serializers.CharField(read_only=True)
    name = serializers.CharField(max_length=254, required=False)
    description = serializers.CharField(required=False)
    issuer = LinkedDataReferenceField(['slug'], Issuer, many=False, read_only=True)
    groups = LinkedDataReferenceField(['slug'], RecipientGroup, many=True, required=False)
    completionBadge = LinkedDataReferenceField(['slug'], BadgeClass, read_only=True, required=False, allow_null=True, source='completion_badge')
    rootChildCount = serializers.IntegerField(read_only=True, source='cached_root_element.pathwayelement_set.count')
    elementCount = serializers.IntegerField(read_only=True, source='pathwayelement_set.count')

    def to_representation(self, instance):
        issuer_slug = instance.cached_issuer.slug

        representation = super(PathwaySerializer, self).to_representation(instance)

        representation['@id'] = instance.jsonld_id
        if self.context.get('include_context', False):
            representation.update([
                ('@context',"https://badgr.io/public/contexts/pathways"),
                ("@type", "Pathway")
            ])

        if self.context.get('include_structure', False):
            self.context.update({
                'pathway_slug': instance.slug,
            })
            element_serializer = PathwayElementSerializer(instance.cached_elements(), many=True, context=self.context)
            representation.update([
                ('rootElement', settings.HTTP_ORIGIN+reverse('pathway_element_detail', kwargs={
                    'issuer_slug': issuer_slug,
                    'pathway_slug': instance.slug,
                    'element_slug': instance.cached_root_element.slug})),
                ('elements', element_serializer.data)
            ])
        return representation

    def create(self, validated_data, **kwargs):
        # TODO: Replace with validate_name and validate_description methods that check for self.instance
        if not validated_data.get('name') or not validated_data.get('description'):
            raise ValidationError("Values for name and description are required to create a Pathway.")

        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Could not determine issuer")
        try:
            issuer = Issuer.cached.get_by_slug_or_id(issuer_slug)
        except Issuer.DoesNotExist:
            raise ValidationError("Could not determine issuer")

        name = validated_data.get('name')

        pathway = Pathway(issuer=issuer)
        pathway.save(name_hint=name)
        root_element = PathwayElement(
            pathway=pathway,
            parent_element=None,
            name=name,
            description=validated_data.get('description'),
        )
        root_element.save()
        pathway.root_element = root_element
        pathway.save()
        return pathway

    def update(self, instance, validated_data):
        if 'groups' in validated_data:
            existing_groups = set(instance.recipient_groups.all())
            updated_groups = set(validated_data.get('groups'))

            groups_to_delete = existing_groups - updated_groups
            groups_to_add = updated_groups - existing_groups

            for g in groups_to_delete:
                instance.recipient_groups.remove(g)

            for g in groups_to_add:
                instance.recipient_groups.add(g)

        instance.save() # update caches, sloppily
        return instance


class PathwayElementSerializer(LinkedDataEntitySerializer):
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.CharField()
    parent = serializers.CharField(required=False)
    alignmentUrl = serializers.CharField(required=False, allow_null=True)
    ordering = serializers.IntegerField(required=False, default=99)
    completionBadge = LinkedDataReferenceField(
        ['slug'],
        BadgeClass,
        read_only=False,
        required=False,
        allow_null=True,
        queryset=BadgeClass.objects.none(),
        source='completion_badgeclass'
    )
    requirements = serializers.DictField(required=False, allow_null=True)

    def to_representation(self, instance):
        include_requirements = self.context.get('include_requirements', True)
        representation = super(PathwayElementSerializer, self).to_representation(instance)

        representation['children'] = [
            child.jsonld_id for child in instance.cached_children()
        ]

        if include_requirements and instance.completion_requirements:
            completion_serializer = PathwayElementCompletionSpecSerializer(instance.completion_requirements, context=self.context)
            representation['requirements'] = completion_serializer.data

        return representation

    def create(self, validated_data):
        pathway_slug = self.context.get('pathway_slug', None)
        if not pathway_slug:
            raise ValidationError("Could not determine pathway")
        try:
            pathway = Pathway.cached.get_by_slug_or_id(pathway_slug)
        except Pathway.DoesNotExist:
            raise ValidationError("Could not determine pathway")

        parent_slug = validated_data.get('parent')
        try:
            parent_element = PathwayElement.cached.get_by_slug_or_id(parent_slug)
        except PathwayElement.DoesNotExist:
            raise ValidationError("Invalid parent")
        else:
            if parent_element.pathway != pathway:
                raise ValidationError("Invalid parent")

        try:
            ordering = int(validated_data.get('ordering', 99))
        except ValueError:
            ordering = 99

        completion_requirements = None
        requirement_string = validated_data.get('requirements', None)
        if requirement_string:
            try:
                completion_requirements = CompletionRequirementSpecFactory.parse(requirement_string).serialize()
            except ValueError as e:
                raise ValidationError("Invalid completion spec: {}".format(e.message))

        element = PathwayElement(pathway=pathway,
                                 parent_element=parent_element,
                                 ordering=ordering,
                                 name=validated_data.get('name'),
                                 description=validated_data.get('description', None),
                                 alignment_url=validated_data.get('alignmentUrl', None),
                                 completion_badgeclass=validated_data.get('completion_badgeclass'),
                                 completion_requirements=completion_requirements)
        element.save()
        return element

    def update(self, element, validated_data):
        parent_element = None
        parent_slug = validated_data.get('parent')
        if parent_slug:
            try:
                parent_element = PathwayElement.cached.get_by_slug_or_id(parent_slug)
            except PathwayElement.DoesNotExist:
                raise ValidationError("Invalid parent")

        completion_requirements = None
        requirements = validated_data.get('requirements')
        if requirements:
            try:
                completion_requirements = CompletionRequirementSpecFactory.parse_obj(requirements).serialize()
            except ValueError as e:
                raise ValidationError("Invalid requirements: {}".format(e))

        child_ids = validated_data.get('children')
        order = 1
        if child_ids:
            for element_id in child_ids:
                try:
                    r = resolve(element_id.replace(settings.HTTP_ORIGIN, ''))
                except Resolver404:
                    raise ValidationError("Invalid child id: {}".format(element_id))

                element_slug = r.kwargs.get('element_slug')

                try:
                    child = PathwayElement.cached.get(slug=element_slug)
                except PathwayElement.DoesNotExist:
                    raise ValidationError("Invalid child id: {}".format(element_id))
                else:
                    child.parent_element = element
                    child.ordering = order
                    order += 1
                    child.save()

        old_parent = None
        if parent_element:
            old_parent = element.parent_element
            element.parent_element = parent_element

        element.completion_badgeclass = validated_data.get('completion_badgeclass')
        element.name = validated_data.get('name')
        element.description = validated_data.get('description')
        element.alignment_url = validated_data.get('alignmentUrl')
        element.ordering = validated_data.get('ordering', 99)
        element.completion_requirements = completion_requirements
        element.save()

        if old_parent:
            old_parent.publish()

        return element


class PathwayElementCompletionSpecSerializer(serializers.Serializer):
    def to_representation(self, instance):
        return instance


class RecipientCompletionSerializer(serializers.Serializer):
    def to_representation(self, instance):
        profile, completions = instance
        return OrderedDict([
            ('recipient', OrderedDict([
                ('@id', profile.jsonld_id),
                ('slug', profile.slug),
                ('recipientGroups', [{'@id': m.recipient_group.jsonld_id, 'slug': m.recipient_group.slug} for m in profile.cached_group_memberships()]),
            ])),
            ('completions', completions)
        ])


class PathwayElementCompletionSerializer(serializers.Serializer):
    def to_representation(self, completions):
        issuer_slug = self.context.get('issuer_slug', None)
        if not issuer_slug:
            raise ValidationError("Invalid issuer_slug")
        pathway_slug = self.context.get('pathway_slug', None)
        if not pathway_slug:
            raise ValidationError("Invalid pathway_slug")
        element_slug = self.context.get('element_slug', None)
        if not element_slug:
            raise ValidationError("Invalid element_slug")

        completions_serializer = RecipientCompletionSerializer(completions.items(), many=True, context=self.context)

        return OrderedDict([
            ("@context", "https://badgr.io/public/contexts/pathways"),
            ("@type", "PathwayElementsCompletionReport"),
            ("rootElement", settings.HTTP_ORIGIN+reverse("pathway_element_detail", kwargs={
                'issuer_slug': issuer_slug,
                'pathway_slug': pathway_slug,
                'element_slug': element_slug
            })),
            ("recipientCompletions", completions_serializer.data),
        ])
