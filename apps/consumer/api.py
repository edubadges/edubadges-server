# Views for Consumer API endpoints. Consumers upload earned badges for analysis.
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from rest_framework import authentication, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError

from models import ConsumerBadge
from serializers import ConsumerBadgeSerializer, ConsumerBadgeDetailSerializer
from badgeanalysis.models import OpenBadge
from badgeanalysis.validation_messages import BadgeValidationError
from mainsite.permissions import IsOwner


class ConsumerBadgesList(APIView):
    """
    GET: Viewing a list of a consumer' badges, or POST to upload a new one to analyze
    """
    model = ConsumerBadge

    # TODO: rich authentication possibilitiesfor remote API clients
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    # permission_classes = (IsOwner,)

    def get(self, request):
        """
        return a list of of badges that the consumer is currently analyzing.
        TODO: make these badges expire after a few days
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_204_NO_CONTENT)

        try:
            consumer_badges = ConsumerBadge.objects.filter(consumer=request.user)
        except ConsumerBadge.DoesNotExist:
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = ConsumerBadgeDetailSerializer(consumer_badges, many=True)

        return Response(serializer.data)

    def post(self, request):
        """
        Add a new badge to a consumer's collection of badges under analysis
        request.data: {
            "badge_input": "http://assertionUrl? or assertion json text blob",
            "image": <File object?>,
            "recipient_input": "user@email.com"
        }
        Must have (either badge_input or image) and recipient_input (unlike EarnerBadge, we can't assume an earner ID from consumer's stored email address)
        """
        if isinstance(request.user, get_user_model()):
            consumer_user = request.user
        else:
            consumer_user = None

        try:
            the_actual_badge = OpenBadge(
                badge_input=request.data.get('badge_input', None),
                recipient_input=request.data.get('recipient_input', None),
                image=request.data.get('image', None)
            )
            the_actual_badge.save()
        except BadgeValidationError as e:
            # Catches the case where the OpenBadge could not be saved because it was not new.
            if e.validator == 'create_only':
                the_actual_badge = OpenBadge.find_by_assertion_iri(e.data, **{'recipient_input': request.user.email})
            else:
                raise ValidationError(e.message)
        except Exception as e:
            raise ValidationError(e.message)

        try:
            new_consumer_badge = ConsumerBadge(
                consumer=consumer_user,
                badge=the_actual_badge
            )
        except ValueError as e:
            # this copied from EarnerBadge... what is this catching again & does it make sense 
            # in the ConsumerBadge context, given that ConsumerBadges may be created by anon users?    
            return Response(status=status.HTTP_403_FORBIDDEN)

        if consumer_user is not None:
            try:
                new_consumer_badge.save()
            except IntegrityError:
                raise ValidationError("This badge has already been uploaded for analysis.")
            except Exception as e:
                raise ValidationError(e.message)

        # Will return serialization of unsaved ConsumerBadge for anon users.
        serializer = ConsumerBadgeDetailSerializer(new_consumer_badge)
        if consumer_user is not None:
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request):
        # TODO: check if user is authenticated and is owner of the ConsumerBadge. Delete if it's all cool.
        pass


class ConsumerBadgeDetail(APIView):
    """
    View a single ConsumerBadge in detail (GET) or update a single ConsumerBadge with PUT
    """
    model = ConsumerBadge

    # TODO: rich authentication possibilitiesfor remote API clients
    authentication_classes = (
        # authentication.TokenAuthentication,
        authentication.SessionAuthentication,
        authentication.BasicAuthentication,
    )
    permission_classes = (IsOwner,)

    def get(self, request, pk):
        """
        Return full details on a single badge the consumer is currently analyzing.
        """
        if not isinstance(request.user, get_user_model()):
            return Response(status=status.HTTP_403_FORBIDDEN)

        try:
            consumer_badge = ConsumerBadge.objects.get(consumer=request.user, pk=pk)
        except ConsumerBadge.DoesNotExist:
            return Response("Badge " + pk + " not found.", status=status.HTTP_404_NOT_FOUND)

        serializer = ConsumerBadgeDetailSerializer(consumer_badge)

        return Response(serializer.data)

    def put(self, resuest, pk):
        pass
