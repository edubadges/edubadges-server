# Created by wiggins@concentricsky.com on 3/30/16.
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.status import HTTP_201_CREATED

from issuer.api import AbstractIssuerAPIEndpoint
from issuer.models import Issuer
from pathway.models import Pathway
from pathway.serializers import PathwaySerializer, PathwayListSerializer


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

        serializer = PathwaySerializer(pathway, context={
            'request': request,
            'issuer_slug': issuer_slug,
            'include_structure': True
        })
        return Response(serializer.data)
