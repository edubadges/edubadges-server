import os

from django.db import IntegrityError

from rest_framework import permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView

import badgrlog
from composition.utils import get_badge_by_identifier
from issuer.models import BadgeInstance
from issuer.public_api import ImagePropertyDetailView
from mainsite.permissions import IsOwner

from .serializers import (LocalBadgeInstanceUploadSerializer,
                          CollectionSerializer, CollectionBadgeSerializer)
from .models import LocalBadgeInstance, Collection, LocalBadgeInstanceCollection, LocalIssuer, LocalBadgeInstanceShare, \
    CollectionShare

logger = badgrlog.BadgrLogger()


class LocalBadgeInstanceList(APIView):
    """
    Retrieve a list of the logged-in user's locally imported badges or post a
    new badge.
    """
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request):
        """
        GET a list of all the logged-in user's locally imported badges.
        ---
        serializer: LocalBadgeInstanceUploadSerializer
        """

        imported_badges = LocalBadgeInstance.objects.filter(recipient_user=request.user)
        local_badges = BadgeInstance.objects.filter(
            recipient_identifier__in=request.user.all_recipient_identifiers
        ).exclude(
            acceptance=BadgeInstance.ACCEPTANCE_REJECTED
        ).exclude(revoked=True)

        local_badge_slugs = [lb.json.get('uid') for lb in local_badges]
        filtered_imported_badges = filter(lambda lbi: lbi.json.get('uid') not in local_badge_slugs, imported_badges)
        user_badges = list(filtered_imported_badges) + list(local_badges)

        serializer = LocalBadgeInstanceUploadSerializer(
            user_badges, many=True, context={
                'request': request,
                'format': request.query_params.get('json_format', 'v1')
            })

        return Response(serializer.data)

    def post(self, request):
        """
        POST badge information to add a badge to the logged-in user's account.
        along with either a badge image file, hosted
        badge assertion URL, or badge assertion content itself.
        ---
        serializer: LocalBadgeInstanceUploadSerializer
        parameters:
            - name: image
              description: A baked badge image file
              required: false
              type: file
              paramType: form
            - name: assertion
              description: The signed or hosted assertion content, either as a JSON string or base64-encoded JWT
              required: false
              type: string
              paramType: form
            - name: url
              description: The URL of a hosted assertion
              required: false
              type: string
              paramType: form
        """
        serializer = LocalBadgeInstanceUploadSerializer(
            data=request.data, context={
                'request': request,
                'format': request.query_params.get('json_format', 'v1')
            })

        serializer.is_valid(raise_exception=True)

        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LocalBadgeInstanceDetail(APIView):
    queryset = LocalBadgeInstance.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    """
    View, accept, or delete a badge earned by the logged-in user.
    """
    def get(self, request, badge_id):
        """
        GET details on one badge.
        ---
        serializer: LocalBadgeInstanceUploadSerializer
        parameters:
            - name: badge_id
              description: the unique id of the earner's badge to view
              required: true
              type: integer
              paramType: path
        """
        user_badge = get_badge_by_identifier(badge_id, user=request.user)
        if user_badge is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = LocalBadgeInstanceUploadSerializer(user_badge, context={
            'request': request,
            'format': request.query_params.get('json_format', 'v1')
        })

        return Response(serializer.data)

    def put(self, request, badge_id):
        user_badge = get_badge_by_identifier(badge_id, user=request.user)
        if user_badge is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        key_set = set(request.data.keys()) - set(['image'])
        data = {key: request.data.get(key) for key in key_set}

        serializer = LocalBadgeInstanceUploadSerializer(
            instance=user_badge, data=data,
            context={
                'request': request,
                'format': request.query_params.get('json_format', 'v1')}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, badge_id):
        """
        DELETE one stored badge from the logged-in earner's collection.
        ---
        parameters:
            - name: badge_id
              description: the unique id of the earner's badge to delete
              required: true
              type: integer
              paramType: path
        """
        user_badge = get_badge_by_identifier(badge_id, user=request.user)
        if user_badge is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if isinstance(user_badge, LocalBadgeInstance):
            user_badge.delete()
        elif isinstance(user_badge, BadgeInstance):
            def _find_local_badge_duplicate(issuer_badge_instance, user):
                for lbi in LocalBadgeInstance.objects.filter(recipient_user=user):
                    if lbi.json.get('uid') == issuer_badge_instance.slug:
                        return lbi
            lbi = _find_local_badge_duplicate(user_badge, request.user)
            if lbi:
                lbi.delete()
            user_badge.acceptance = BadgeInstance.ACCEPTANCE_REJECTED
            user_badge.save()

        return Response(status=status.HTTP_204_NO_CONTENT)



class CollectionLocalBadgeInstanceList(APIView):
    """
    POST to add badges to collection, PUT to update collection to a new list of
    ids.
    """
    queryset = LocalBadgeInstanceCollection.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, slug):
        """
        GET the badges in a single Collection
        """
        collection_badges = self.queryset.filter(
            collection__slug=slug,
            instance__recipient_user=request.user)

        serializer = CollectionBadgeSerializer(
            collection_badges, many=True)

        return Response(serializer.data)

    def post(self, request, slug):
        """
        POST new badge(s) to add them to a existing Collection.
        Returns resulting complete list of collection contents.
        """
        try:
            collection = Collection.objects.get(owner=request.user, slug=slug)
        except (Collection.MultipleObjectsReturned, Collection.DoesNotExist):
            return Response("Badge collection %s not found." % slug,
                            status=status.HTTP_404_NOT_FOUND)

        add_many = isinstance(request.data, list)
        serializer = CollectionBadgeSerializer(
            data=request.data, many=add_many,
            context={
                'collection': collection,
                'request': request, 'user': request.user,
                'add_only': True
            }
        )
        serializer.is_valid(raise_exception=True)

        new_records = serializer.save()

        if new_records == []:
            return Response(
                "No new records could be added to collection. " +
                "Check for missing/unknown badge references, unauthorized " +
                "access, or badges already existing in collection.",
                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request, slug):
        """
        Update the list of badges included in a collection among
        those added to the logged-in user's badges. Cannot be used to
        change the description of a badge in the collection, but can
        be used to add descriptions to new badges to be added from the
        user's existing badges. Cannot be used to add new badges to the
        user's account at this time.
        ---
        parameters:
            - name: slug
              description: The collection's slug identifier
              required: true
              type: string
              paramType: path
            - name: badges
              description: A JSON serialization of all the badges to be included in this collection, replacing the list that currently exists.
              required: true
              paramType: body
        """
        badges = request.data

        try:
            collection = Collection.objects.get(
                owner=request.user,
                slug=slug)
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CollectionBadgeSerializer(
            data=badges, many=True, context={'collection': collection})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


class CollectionLocalBadgeInstanceDetail(APIView):
    """
    Update details on a single item in the collection or remove it from the
    collection.
    """
    queryset = LocalBadgeInstanceCollection.objects.all()
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request, collection_slug, badge_id):
        try:
            item = self.queryset.get(
                instance__recipient_user=request.user,
                collection__slug=collection_slug,
                instance__id=int(badge_id))
        except LocalBadgeInstanceCollection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CollectionBadgeSerializer(item)
        return Response(serializer.data)

    def put(self, request, collection_slug, badge_id):
        """
        Update the description of a badge in a collection.
        ---
        parameters:
            - name: description
              description: Earner's annotation about a badge particular to this collection's audience.
              required: true
              type: string
              paramType: form
            - name: collection_slug
              description: The collection's slug identifier
              required: true
              type: string
              paramType: path
            - name: badge_id
              description: The stored badge's integer identifier
              required: true
              type: integer
              paramType: path
        """
        description = request.data.get('description', '')

        try:
            description = str(description)
        except TypeError:
            return serializers.ValidationError(
                "Server could not understand description")
        try:
            item = self.queryset.get(
                instance__recipient_user=request.user,
                collection__slug=collection_slug,
                instance__id=int(badge_id))
        except LocalBadgeInstanceCollection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        item.description = description
        item.save()

        serializer = CollectionBadgeSerializer(item)
        return Response(serializer.data)

    def delete(self, request, collection_slug, badge_id):
        """
        Remove a badge from a collection (does not delete it
        from the earner's account)
        ---
        parameters:
            - name: collection_slug
              description: The collection's slug identifier
              required: true
              type: string
              paramType: path
            - name: badge_id
              description: The stored badge's integer identifier
              required: true
              type: integer
              paramType: path
        """
        try:
            self.queryset.get(
                instance__recipient_user=request.user,
                collection__slug=collection_slug,
                instance__id=int(badge_id)
            ).delete()
        except LocalBadgeInstanceCollection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionDetail(APIView):
    """
    View details of one Collection, update or delete it.
    """
    queryset = Collection.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request, slug):
        """
        GET a single collection details, by slug
        """
        try:
            user_collection = self.queryset.get(
                owner=request.user,
                slug=slug
            )
        except (Collection.MultipleObjectsReturned,
                Collection.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = CollectionSerializer(user_collection)
            return Response(serializer.data)

    def put(self, request, slug):
        """
        Update a badge collection's metadata and/or badge list.
        ---
        serializer: CollectionSerializer
        parameters:
            - name: slug
              description: The collection's slug identifier
              required: true
              type: string
              paramType: path
            - name: description
              description: A description of the collection.
              required: false
              type: string
              paramType: form
            - name: badges
              type: array
              items: {
                type: string
              }
        """

        try:
            collection = self.queryset.get(
                owner=request.user,
                slug=slug
            )
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = CollectionSerializer(collection, data=request.data, context={
            'request': request, 'user': request.user,
            'collection': collection
        }, partial=True)

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)

    def delete(self, request, slug):
        """
        Delete a collection
        ---
        parameters:
            - name: slug
              description: "The collection's slug identifier"
              type: string
              paramType: path
        """
        try:
            user_collection = self.queryset.get(
                owner=request.user,
                slug=slug
            )
        except (Collection.MultipleObjectsReturned,
                Collection.DoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            user_collection.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)


class CollectionList(APIView):
    """
    Retrieve a list of Collections or post to create a new collection.
    """
    queryset = Collection.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request):
        """
        GET a list of the logged-in user's Collections.
        ---
        serializer: CollectionSerializer
        parameters:
            - name: badges
              type: array
              items: {
                type: string
              }
        """
        user_collections = self.queryset.filter(owner=request.user)

        serializer = CollectionSerializer(user_collections, many=True,
                                          context={'request': request, 'user': request.user})

        return Response(serializer.data)

    def post(self, request):
        """
        POST a new collection to the logged-in user's account.
        ---
        serializer: CollectionSerializer
        parameters:
            - name: badges
              type: array
              items: {
                type: string
              }
        """
        serializer = CollectionSerializer(
            data=request.data,
            context={
                'request': request,
                'user': request.user
            }
        )

        serializer.is_valid(raise_exception=True)
        try:
            serializer.save()
        except IntegrityError:
            return Response("A collection with this name already exists",
                            status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CollectionGenerateShare(APIView):
    """
    Allows a Collection to be public by generation of a shareable hash.
    """
    queryset = Collection.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request, slug):
        try:
            collection = self.queryset.get(
                owner=request.user,
                slug=slug)
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        collection.published = True
        collection.save()

        return Response(collection.share_url)

    def delete(self, request, slug):
        try:
            collection = self.queryset.get(
                owner=request.user,
                slug=slug)
        except Collection.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        collection.share_hash = ''
        collection.save()

        return Response(status=status.HTTP_204_NO_CONTENT)


class LocalBadgeInstanceImage(ImagePropertyDetailView):
    model = LocalBadgeInstance
    prop = 'image'


class LocalIssuerImage(ImagePropertyDetailView):
    model = LocalIssuer
    prop = 'image_preview'


class ShareBadge(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, badge_id):
        """
        Share a single badge to a support share provider
        ---
        parameters:
            - name: badge_id
              description: The identifier of a badge returned from /v1/earner/badges
              required: true
              type: string
              paramType: path
            - name: provider
              description: The identifier of the provider to use. Supports 'facebook', 'linkedin'
              required: true
              type: string
              paramType: query
        """
        provider = request.query_params.get('provider')

        badge = get_badge_by_identifier(badge_id)
        if badge is None:
            return Response(status=status.HTTP_404_NOT_FOUND)

        share = LocalBadgeInstanceShare(provider=provider)
        share.set_badge(badge)
        share_url = share.get_share_url(provider)
        if not share_url:
            return Response({'error': "invalid share provider"}, status=status.HTTP_400_BAD_REQUEST)

        share.save()
        headers = {'Location': share_url}
        return Response(status=status.HTTP_302_FOUND, headers=headers)


class ShareCollection(APIView):
    permission_classes = (permissions.AllowAny,)

    def get(self, request, collection_slug):
        """
        Share a collection to a supported share provider
        ---
        parameters:
            - name: collection_slug
              description: The identifier of a collection
              required: true
              type: string
              paramType: path
            - name: provider
              description: The identifier of the provider to use. Supports 'facebook', 'linkedin'
              required: true
              type: string
              paramType: query
        """
        provider = request.query_params.get('provider')

        collection = Collection.cached.get(slug=collection_slug)
        if collection.owner != request.user:
            return Response(status=status.HTTP_404_NOT_FOUND)

        share = CollectionShare(provider=provider, collection=collection)
        share_url = share.get_share_url(provider, title=collection.name, summary=collection.description)
        if not share_url:
            return Response({'error': "invalid share provider"}, status=status.HTTP_400_BAD_REQUEST)

        share.save()
        headers = {'Location': share_url}
        return Response(status=status.HTTP_302_FOUND, headers=headers)
