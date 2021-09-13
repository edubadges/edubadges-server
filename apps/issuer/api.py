import badgrlog
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND, HTTP_200_OK, HTTP_400_BAD_REQUEST

from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin, BaseEntityView, BaseArchiveView
from issuer.models import Issuer, BadgeClass, BadgeInstance, BadgeInstanceCollection
from issuer.permissions import AwardedAssertionsBlock
from issuer.serializers import IssuerSerializer, BadgeClassSerializer, BadgeInstanceSerializer, \
    BadgeInstanceCollectionSerializer
from mainsite.exceptions import BadgrApiException400, BadgrValidationFieldError
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from signing import tsob
from signing.models import AssertionTimeStamp
from signing.permissions import MaySignAssertions
from staff.permissions import HasObjectPermission

logger = badgrlog.BadgrLogger()


class BadgeClassList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a new BadgeClass
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = BadgeClassSerializer
    http_method_names = ['post']


class IssuerList(VersionedObjectMixin, BaseEntityListView):
    """
    POST to create a new Issuer
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)   # permissioned in serializer
    v1_serializer_class = IssuerSerializer
    http_method_names = ['post']


class BadgeClassDeleteView(BaseArchiveView):
    model = BadgeClass
    v1_serializer_class = BadgeClassSerializer


class IssuerDeleteView(BaseArchiveView):
    model = Issuer
    v1_serializer_class = IssuerSerializer


class BadgeClassDetail(BaseEntityDetailView):
    model = BadgeClass
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission, AwardedAssertionsBlock)
    v1_serializer_class = BadgeClassSerializer
    http_method_names = ['put']


class IssuerDetail(BaseEntityDetailView):
    model = Issuer
    v1_serializer_class = IssuerSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    http_method_names = ['put']


class TimestampedBadgeInstanceList(BaseEntityListView):
    http_method_names = ['get', 'delete']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)
    serializer_class = BadgeInstanceSerializer

    def get(self, request, **kwargs):
        return super(TimestampedBadgeInstanceList, self).get(request, **kwargs)

    def get_objects(self, request, **kwargs):
        return request.user.get_assertions_ready_for_signing()

    def delete(self, request, **kwargs):
        badge_instance_slug = request.data.get('badge_instance_slug')
        badge_instance = BadgeInstance.objects.get(entity_id=badge_instance_slug)
        assertion_timestamp = AssertionTimeStamp.objects.get(badge_instance=badge_instance)
        if assertion_timestamp.signer != request.user:
            raise ValidationError('You can only delete your own timestamped badges.')
        badge_instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class BatchSignAssertions(BaseEntityListView):
    http_method_names = ['post']
    permission_classes = (AuthenticatedWithVerifiedEmail, MaySignAssertions)
    serializer_class = BadgeInstanceSerializer

    def post(self, request, **kwargs):
        # post assertions to be signed
        password = request.data.get('password')
        assertion_slugs = [instance['slug'] for instance in request.data.get('badge_instances')]
        user = request.user
        if not password:
            raise ValidationError('Cannot sign badges: no password provided.')
        if not assertion_slugs:
            raise ValidationError('No badges to sign.')
        assertion_instances = []
        batch_of_assertion_json = []
        for ass_slug in assertion_slugs:  # pun intended
            assertion_instance = BadgeInstance.objects.get(entity_id=ass_slug)
            if not user.may_sign_assertion(assertion_instance):
                raise ValidationError('You do not have permission to sign this badge.')
            if not user in [staff.user for staff in assertion_instance.issuer.current_signers]:
                raise ValidationError('You are not a signer for this issuer: {}'.format(assertion_instance.issuer.name))
            if assertion_instance.signature:
                raise ValidationError('Cannot sign Assertion for Badgeclass {} with recipient identifier {}. Assertion already signed.'.format(assertion_instance.badgeclass.name, assertion_instance.recipient_identifier))
            assertion_instances.append(assertion_instance)

            timestamp = AssertionTimeStamp.objects.get(badge_instance=assertion_instance)
            js = timestamp.get_json_with_proof()
            batch_of_assertion_json.append(js)
        successful_assertions = []
        user.current_symmetric_key.validate_password(password)
        try:
            private_key = tsob.create_new_private_key(password, user.current_symmetric_key)
        except ValueError as e:
            raise ValidationError(str(e))
        try:
            signed_badges = tsob.sign_badges(batch_of_assertion_json,
                                             private_key,
                                             user.current_symmetric_key,
                                             password)
        except ValueError as e:
            raise ValidationError(str(e))
        for signed_badge in signed_badges:
            signature = signed_badge['signature']
            matching_assertion = [ass for ass in assertion_instances if ass.identifier == signed_badge['plain_badge']['id']]
            if len(matching_assertion) > 1:
                raise ValidationError('Signing failed: Signed json could not be matched to a BadgeInstance')
            matching_assertion = matching_assertion[0]
            matching_assertion.rebake(signature=signature, replace_image=True, save=False)
            matching_assertion.signature = signature
            matching_assertion.public_key_issuer.public_key = private_key.public_key
            matching_assertion.public_key_issuer.save()
            matching_assertion.save()
            AssertionTimeStamp.objects.get(badge_instance=matching_assertion).delete()
            # matching_assertion.notify_earner(attach_image=True)
            successful_assertions.append(matching_assertion)
        serializer_class = self.get_serializer_class()
        serializer_instance = serializer_class()
        response = [serializer_instance.to_representation(assertion) for assertion in successful_assertions]
        return Response(status=status.HTTP_201_CREATED, data=response)


class BatchAwardEnrollments(VersionedObjectMixin, BaseEntityView):
    model = BadgeClass  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = BadgeInstanceSerializer
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    def post(self, request, **kwargs):
        # verify the user has permission to the badgeclass
        badgeclass = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, badgeclass):
            return Response(status=HTTP_404_NOT_FOUND)
        request.data['badgeclass'] = badgeclass
        try:
            request.data.get('create_notification', False)
        except AttributeError:
            return Response(status=HTTP_400_BAD_REQUEST)

        # save serializers
        context = self.get_context_data(**kwargs)
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(many=True, data=request.data.get('enrollments'), context=context)
        serializer.is_valid(raise_exception=True)
        new_instances = serializer.save(created_by=request.user)
        for new_instance in new_instances:
            self.log_create(new_instance)
        # Clear cache for the enrollments of this badgeclass
        badgeclass.remove_cached_data(['cached_pending_enrollments'])
        badgeclass.remove_cached_data(['cached_pending_enrollments_including_denied'])
        badgeclass.remove_cached_data(['cached_assertions'])
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BadgeInstanceRevoke(BaseEntityDetailView):
    """
    Endpoint for revoking a badge (DELETE)
    """
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ['post']
    permission_map = {'POST': 'may_award'}

    def post(self, request, **kwargs):
        revocation_reason = request.data.get('revocation_reason', None)
        if not revocation_reason:
            raise BadgrValidationFieldError('revocation_reason', "This field is required", 999)
        assertions = request.data.get('assertions', None)
        if not assertions:
            raise BadgrValidationFieldError('assertions', "This field is required", 999)
        for assertion in assertions:
            badgeinstance = BadgeInstance.objects.get(entity_id=assertion['entity_id'])
            if badgeinstance.get_permissions(request.user)['may_award']:
                badgeinstance.revoke(revocation_reason)
            else:
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result":"ok"}, status=status.HTTP_200_OK)


class BadgeInstanceCollectionDetail(BaseEntityDetailView):
    model = BadgeInstanceCollection
    serializer_class = BadgeInstanceCollectionSerializer
    permission_classes = (AuthenticatedWithVerifiedEmail, )
    http_method_names = ['delete','put']


class BadgeInstanceCollectionDetailList(BaseEntityListView):
    model = BadgeInstanceCollection
    permission_classes = (AuthenticatedWithVerifiedEmail,)   # permissioned in serializer
    v1_serializer_class = BadgeInstanceCollectionSerializer
    http_method_names = ['post']
