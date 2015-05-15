from rest_framework import authentication, permissions, status, serializers
from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from mainsite.permissions import IsOwner
from credential_store.models import StoredBadgeInstance

from .serializers import (EarnerBadgeSerializer,
                          EarnerBadgeReferenceSerializer,
                          CollectionSerializer)
from .models import Collection


class EarnerBadgeList(APIView):
    """
    Retrieve a list of user's earned badges or post a new badge.
    """
    queryset = StoredBadgeInstance.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request):
        """
        GET a list of all the logged-in user's earned badges
        ---
        serializer: EarnerBadgeSerializer
        """
        user_badges = self.queryset.filter(recipient_user=request.user)

        serializer = EarnerBadgeSerializer(
            user_badges, many=True, context={'request': request}
        )

        return Response(serializer.data)

    def post(self, request):
        """
        POST badge information to add a badge to the logged-in user's account.
        Badgealong with either a badge image file, hosted
        badge assertion URL, or badge assertion content itself.
        ---
        serializer: EarnerBadgeSerializer
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
            - name: image
              description: A baked badge image PNG
              required: false
              type: file
              paramType: form
        """
        serializer = EarnerBadgeSerializer(data=request.data, context={'request': request})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        # if serializer.instance.version is None:
        #     return Response()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EarnerCollectionList(APIView):
    """
    Retrieve a list of Collections or post to create a new collection
    """
    queryset = Collection.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request):
        """
        GET a list of the logged-in user's Collections.
        ---
        serializer: CollectionSerializer
        """
        user_collections = self.queryset.filter(recipient=request.user)

        serializer = CollectionSerializer(
            user_collections, many=True, context={'request': request}
        )

        return Response(serializer.data)

    def post(self, request):
        """
        POST a new collection to the logged-in user's account.
        ---
        serializer: CollectionSerializer
        """
        serializer = CollectionSerializer(
            data=request.data, context={'request': request}
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=status.HTTP_201_CREATED)


class EarnerCollectionDetail(APIView):
    """
    View details of one Collection, update or delete it
    """
    queryset = Collection.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request, slug):
        """
        GET a single collection details, by slug
        """
        try:
            user_collection = self.queryset.get(
                recipient=request.user,
                slug=slug
            )
        except (Collection.MultipleObjectsReturned,
                Collection.ObjectDoesNotExist):
            return Response(status=status.HTTP_404_NOT_FOUND)

        else:
            serializer = CollectionSerializer(user_collection)
            return Response(serializer.data)


class EarnerCollectionBadgesList(APIView):
    """
    POST to add badges to collection, PUT to update collection to a
    new list of ids.
    """
    queryset = StoredBadgeInstance.objects.all()
    permission_classes = (permissions.IsAuthenticated, IsOwner,)

    def get(self, request, slug):
        """
        GET the badges in a single Collection
        """
        collection_badges = self.queryset.filter(
            collection__slug=slug, recipient_user=request.user
        )

        serializer = EarnerBadgeReferenceSerializer(collection_badges, many=True)
        return Response(serializer.data)

    def post(self, request, slug):
        """
        POST new badge(s) to add them to a existing Collection
        """
        import pdb; pdb.set_trace();
        try:
            collection = Collection.objects.get(
                recipient=request.user, slug=slug
            )
        except (Collection.MultipleObjectsReturned,
                Collection.ObjectDoesNotExist):
            return Response(
                "Badge collection %s not found." % slug,
                status=status.HTTP_404_NOT_FOUND
            )

        add_many = isinstance(request.data, list)
        try:
            serializer = EarnerBadgeReferenceSerializer(
                data=request.data, many=add_many
            )
            serializer.is_valid(raise_exception=True)

            ddd = [x.get('id') for x in request.data]
            eee = self.queryset.filter(recipient_user=request.user, id__in=ddd)
            fff =[StoredBadgeInstanceCollection(instance=y, collection=collection) for y in eee]
            StoredBadgeInstanceCollection.objects.bulk_create(fff)

            return self.get(request, slug)

        except serializers.ValidationError as e:
            raise e
        else:
            pass
