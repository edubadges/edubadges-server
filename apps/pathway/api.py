# Created by wiggins@concentricsky.com on 3/30/16.
from rest_framework import status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from issuer.api import AbstractIssuerAPIEndpoint
from issuer.models import Issuer, BadgeClass
from pathway.completionspec import CompletionRequirementSpec
from pathway.models import Pathway, PathwayElement, PathwayElementBadge
from pathway.serializers import PathwaySerializer, PathwayListSerializer, PathwayElementSerializer, \
    PathwayElementBadgeSerializer, PathwayElementBadgeListSerializer


class PathwayList(AbstractIssuerAPIEndpoint):

    def get(self, request, issuer_slug):
        """
        GET a list of learning pathways owned by an issuer
        ---
        serializer: PathwaySerializer
        """

        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return Response("Could not find issuer", status=status.HTTP_404_NOT_FOUND)

        pathways = issuer.cached_pathways()
        serializer = PathwayListSerializer(pathways, context={
            'request': request,
            'issuer_slug': issuer_slug,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug):
        """
        Define a new pathway to be owned by an issuer
        ---
        parameters:
            - name: name
              description: The name of the new Pathway
              required: true
              type: string
              paramType: form
            - name: description
              description: A short description of the new Pathway
              required: true
              type: string
              paramType: form
            - name: alignmentUrl
              description: An optional URL that points to an external standard
              required: false
              type: string
              paramType: form
        """
        serializer = PathwaySerializer(data=request.data, context={
            'request': request,
            'issuer_slug': issuer_slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        pathway = serializer.data

        # logger.event(badgrlog.PathwayCreatedEvent(pathway))
        return Response(pathway, status=HTTP_201_CREATED)


class PathwayAPIEndpoint(AbstractIssuerAPIEndpoint):
    def _get_issuer_and_pathway(self, issuer_slug, pathway_slug):
        try:
            issuer = Issuer.cached.get(slug=issuer_slug)
        except Issuer.DoesNotExist:
            return None, None
        try:
            self.check_object_permissions(self.request, issuer)
        except PermissionDenied:
            return None, None

        try:
            pathway = Pathway.cached.get(slug=pathway_slug)
        except Pathway.DoesNotExist:
            return issuer, None
        if pathway.issuer != issuer:
            return issuer, None

        return issuer, pathway


class PathwayDetail(PathwayAPIEndpoint):

    def get(self, request, issuer_slug, pathway_slug):
        """
        GET detail on a pathway
        ---
        """
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pathway.issuer != issuer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwaySerializer(pathway, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True
        })
        return Response(serializer.data)


class PathwayElementList(PathwayAPIEndpoint):
    def get(self, request, issuer_slug, pathway_slug):
        """
        GET a flat list of Pathway Elements defined on a pathway
        ---
        """
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if pathway.issuer != issuer:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwaySerializer(pathway, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True,
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug, pathway_slug):
        """
        Add a new Pathway Element
        ---
        serializer: PathwayElementSerializer
        parameters:
            - name: parent
              description: The slug of the parent Pathway Element to attach to
              type: string
              required: true
              paramType: form
            - name: name
              description: The name of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: description
              description: The description of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: ordering
              description: The child order of this Pathway Element relative to its siblings
              type: number
              required: false
              default: 99
              paramType: form
            - name: alignmentUrl
              description: The external Alignment URL this Element aligns to
              type: string
              required: false
              paramType: form
            - name: completionBadge
              description: The slug of the Badge Class to award when element is completed
              type: string
              required: false
              paramType: form
        """
        serializer = PathwayElementSerializer(data=request.data, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
        })
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        element = serializer.data

        # logger.event(badgrlog.PathwayCreatedEvent(pathway))
        return Response(element, status=HTTP_201_CREATED)


class PathwayElementAPIEndpoint(PathwayAPIEndpoint):
    def _get_issuer_and_pathway_element(self, issuer_slug, pathway_slug, element_slug):
        issuer, pathway = self._get_issuer_and_pathway(issuer_slug, pathway_slug)
        if issuer is None or pathway is None:
            return None, None, None

        try:
            element = PathwayElement.cached.get(slug=element_slug)
        except PathwayElement.DoesNotExist:
            return issuer, pathway, None
        if element.pathway != pathway:
            return issuer, pathway, None

        return issuer, pathway, element


class PathwayElementDetail(PathwayElementAPIEndpoint):
    def get(self, request, issuer_slug, pathway_slug, element_slug):
        """
        GET detail on a pathway, starting at a particular Pathway Element
        ---
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwayElementSerializer(element, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True
        })
        return Response(serializer.data)

    def put(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Update a Pathway Element
        ---
        serializer: PathwayElementSerializer
        parameters:
            - name: parent
              description: The slug of the parent Pathway Element to attach to
              type: string
              required: true
              paramType: form
            - name: name
              description: The name of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: description
              description: The description of the Pathway Element
              type: string
              required: true
              paramType: form
            - name: ordering
              description: The child order of this Pathway Element relative to its siblings
              type: number
              required: false
              default: 99
              paramType: form
            - name: alignmentUrl
              description: The external Alignment URL this Element aligns to
              type: string
              required: false
              paramType: form
            - name: completionBadge
              description: The slug of the Badge Class to award when element is completed
              type: string
              required: false
              paramType: form
            - name: requirements
              description: The CompletionRequirementSpec for the element
              type: json
              required: false
              paramType: form
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        parent_element = None
        try:
            parent_element = PathwayElement.cached.get(slug=request.data.get('parent'))
        except PathwayElement.DoesNotExist:
            raise ValidationError("Invalid parent")

        completion_badge = None
        badge_slug = request.data.get('completionBadge', None)
        if badge_slug:
            try:
                completion_badge = BadgeClass.cached.get(slug=badge_slug)
            except BadgeClass.DoesNotExist:
                raise ValidationError("Invalid completionBadge")

        completion_requirements = None
        requirements = request.data.get('requirements', None)
        if requirements:
            try:
                completion_requirements = CompletionRequirementSpec.parse(requirements).serialize()
            except ValueError as e:
                raise ValidationError("Invalid requirements: {}".format(e))

        element.parent_element = parent_element
        element.completion_badge = completion_badge
        element.name = request.data.get('name')
        element.description = request.data.get('description')
        element.alignment_url = request.data.get('alignmentUrl')
        element.ordering = int(request.data.get('ordering', 99))
        element.completion_requirements = completion_requirements
        element.save()
        serializer = PathwayElementSerializer(element, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'include_structure': True
        })
        return Response(serializer.data)

    def delete(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Delete a Pathway Element
        ---
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        element.delete()
        return Response(status=status.HTTP_200_OK)


class PathwayElementBadgesList(PathwayElementAPIEndpoint):
    def get(self, request, issuer_slug, pathway_slug, element_slug):
        """
        GET list of Badge Classes aligned to a Pathway Element
        ---
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = PathwayElementBadgeListSerializer(element.cached_badges(), context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'element_slug': element_slug
        })
        return Response(serializer.data)

    def post(self, request, issuer_slug, pathway_slug, element_slug):
        """
        Add a Badge Class to a Pathway Element
        ---
        parameters:
            - name: badge
              description: The slug of the Badge Class to align
              type: string
              required: true
              paramType: form
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            badgeclass = BadgeClass.cached.get(slug=request.data.get('badge'))
        except BadgeClass.DoesNotExist:
            raise ValidationError("Invalid badge")

        element_badge, created = PathwayElementBadge.cached.get_or_create(pathway=pathway,
                                                                          element=element,
                                                                          badgeclass=badgeclass)
        serializer = PathwayElementBadgeSerializer(element_badge, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'pathway_slug': pathway_slug,
            'element_slug': element_slug
        })
        return Response(serializer.data)


class PathwayElementBadgesDetail(PathwayElementAPIEndpoint):

    def delete(self, request, issuer_slug, pathway_slug, element_slug, badge_slug):
        """
        Remove a Badge Class alignment from a Pathway Element
        """
        issuer, pathway, element = self._get_issuer_and_pathway_element(issuer_slug, pathway_slug, element_slug)
        if issuer is None or pathway is None or element is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            badgeclass = BadgeClass.cached.get(slug=badge_slug)
        except BadgeClass.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            element_badge = PathwayElementBadge.cached.get(element=element, badgeclass=badgeclass)
        except PathwayElementBadge.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        element_badge.delete()
        return Response(status=status.HTTP_200_OK)
