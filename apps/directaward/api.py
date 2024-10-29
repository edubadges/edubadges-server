import datetime
import threading

from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from directaward.models import DirectAward, DirectAwardBundle
from directaward.permissions import IsDirectAwardOwner
from directaward.serializer import DirectAwardSerializer, DirectAwardBundleSerializer
from directaward.signals import audit_trail_signal
from entity.api import BaseEntityListView, BaseEntityDetailView, VersionedObjectMixin
from mainsite import settings
from mainsite.exceptions import (
    BadgrValidationError,
    BadgrValidationFieldError,
    BadgrApiException400,
)
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail
from staff.permissions import HasObjectPermission


class DirectAwardBundleList(VersionedObjectMixin, BaseEntityListView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    v1_serializer_class = DirectAwardBundleSerializer
    permission_map = {"POST": "may_award"}
    http_method_names = ["post"]


class DirectAwardBundleView(APIView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    permission_map = {"POST": "may_award"}

    def get(self, request, **kwargs):
        award_bundle = DirectAwardBundle.objects.get(entity_id=kwargs.get("entity_id"))

        def convert_direct_award(direct_award):
            return {
                "recipient_email": direct_award.recipient_email,
                "eppn": direct_award.eppn,
                "status": direct_award.status,
                "entity_id": direct_award.entity_id,
            }

        def convert_badge_assertion(badge_instance):
            return {
                "full_name": badge_instance.user.full_name,
                "email": badge_instance.user.email,
                "public": badge_instance.public,
                "revoked": badge_instance.revoked,
                "entity_id": badge_instance.entity_id,
                "eppn": badge_instance.user.eppns[0]
            }

        results = {
            "initial_total": award_bundle.initial_total,
            "status": award_bundle.status,
            "badgeclass": award_bundle.badgeclass.name,
            "assertion_count": award_bundle.assertion_count,
            "direct_award_count": award_bundle.direct_award_count,
            "direct_award_rejected_count": award_bundle.direct_award_rejected_count,
            "direct_award_scheduled_count": award_bundle.direct_award_scheduled_count,
            "direct_award_deleted_count": award_bundle.direct_award_deleted_count,
            "direct_award_revoked_count": award_bundle.direct_award_revoked_count,
            "direct_awards": [
                convert_direct_award(da) for da in award_bundle.directaward_set.all()
            ],
            "badge_assertions": [
                convert_badge_assertion(ba)
                for ba in award_bundle.badgeinstance_set.all()
            ],
        }

        return Response(results, status=status.HTTP_200_OK)


class DirectAwardRevoke(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)  # permissioned in serializer
    http_method_names = ["post"]
    permission_map = {"POST": "may_award"}

    @extend_schema(
        request=inline_serializer(
            name="DirectAwardRevokeSerializer",
            fields={
                "revocation_reason": serializers.CharField(),
                "direct_awards": serializers.ListField(
                    child=inline_serializer(
                        name="NestedInlineOneOffSerializer",
                        fields={
                            "entity_id": serializers.CharField(),
                        },
                        allow_null=False,
                    )
                ),
            },
        ),
    )
    def post(self, request, **kwargs):
        """
        Revoke direct awards
        """
        revocation_reason = request.data.get("revocation_reason", None)
        direct_awards = request.data.get("direct_awards", None)
        if not revocation_reason:
            raise BadgrValidationFieldError(
                "revocation_reason", "This field is required", 999
            )
        if not direct_awards:
            raise BadgrValidationFieldError(
                "direct_awards", "This field is required", 999
            )
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award["entity_id"])
            if direct_award.get_permissions(request.user)["may_award"]:
                try:
                    direct_award.revoke(revocation_reason)
                except BadgrValidationError as err:
                    audit_trail_signal.send(
                        sender=request.user.__class__,
                        request=request,
                        user=request.user,
                        method="REVOKE",
                        direct_award_id=direct_award.entity_id,
                        summary="Directaward already revoked or reason not provided",
                    )
                    raise err
                direct_award.bundle.remove_cached_data(["cached_direct_awards"])
                direct_award.badgeclass.remove_cached_data(["cached_direct_awards"])
                direct_award.badgeclass.remove_cached_data(
                    ["cached_direct_award_bundles"]
                )
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="REVOKE",
                    direct_award_id=direct_award.entity_id,
                    summary=f"Directaward revoked with reason {revocation_reason}",
                )
            else:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="REVOKE",
                    direct_award_id=direct_award.entity_id,
                    summary="No permission to revoke directaward",
                )
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result": "ok"}, status=status.HTTP_200_OK)


class DirectAwardResend(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ["post"]
    permission_map = {"POST": "may_award"}

    @extend_schema(
        request=inline_serializer(
            name="DirectAwardResendSerializer",
            fields={
                "direct_awards": serializers.ListField(
                    child=inline_serializer(
                        name="NestedInlineOneOffSerializer",
                        fields={
                            "entity_id": serializers.CharField(),
                        },
                        allow_null=False,
                    )
                )
            },
        ),
    )
    def post(self, request, **kwargs):
        direct_awards = request.data.get("direct_awards", None)
        if not direct_awards:
            raise BadgrValidationFieldError(
                "direct_awards", "This field is required", 999
            )
        successful_direct_awards = []
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award["entity_id"])
            direct_award.resend_at = datetime.datetime.now()
            direct_award.save()
            direct_award.badgeclass.remove_cached_data(["cached_direct_awards"])
            direct_award.bundle.remove_cached_data(["cached_direct_awards"])
            if direct_award.get_permissions(request.user)["may_award"]:
                successful_direct_awards.append(direct_award)
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="RESEND",
                    direct_award_id=direct_award.entity_id,
                    summary="Directaward resent",
                )
            else:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="RESEND",
                    direct_award_id=direct_award.entity_id,
                    summary="No permission to resend directaward",
                )
                raise BadgrApiException400("You do not have permission", 100)

        def send_mail(awards):
            for da in awards:
                da.notify_recipient()

        thread = threading.Thread(target=send_mail, args=(successful_direct_awards,))
        thread.start()

        return Response({"result": "ok"}, status=status.HTTP_200_OK)


class DirectAwardDetail(BaseEntityDetailView):
    model = DirectAward
    permission_classes = (AuthenticatedWithVerifiedEmail, HasObjectPermission)
    v1_serializer_class = DirectAwardSerializer
    http_method_names = ["put"]
    permission_map = {"PUT": "may_award"}


class DirectAwardAccept(BaseEntityDetailView):
    model = DirectAward  # used by .get_object()
    permission_classes = (AuthenticatedWithVerifiedEmail, IsDirectAwardOwner)
    http_method_names = ["post"]

    def post(self, request, **kwargs):
        directaward = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, directaward):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get("accept", False):  # has accepted it
            if not directaward.badgeclass.terms_accepted(request.user):
                raise BadgrValidationError(
                    "Cannot accept direct award, must accept badgeclass terms first",
                    999,
                )
            try:
                assertion = directaward.award(recipient=request.user)
            except BadgrValidationError as err:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="ACCEPT",
                    direct_award_id=directaward.entity_id,
                    summary="Cannot award as eppn does not match or not member of institution",
                )
                raise err
            directaward.badgeclass.remove_cached_data(["cached_direct_awards"])
            directaward.bundle.remove_cached_data(["cached_direct_awards"])
            directaward.delete()
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method="ACCEPT",
                direct_award_id=directaward.entity_id,
                summary="Accepted directaward",
            )
            return Response(
                {"entity_id": assertion.entity_id}, status=status.HTTP_201_CREATED
            )
        elif not request.data.get("accept", True):  # has rejected it
            directaward.status = DirectAward.STATUS_REJECTED  # reject it
            directaward.save()
            directaward.badgeclass.remove_cached_data(["cached_direct_awards"])
            directaward.bundle.remove_cached_data(["cached_direct_awards"])
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method="ACCEPT",
                direct_award_id=directaward.entity_id,
                summary="Rejected directaward",
            )
            return Response({"rejected": True}, status=status.HTTP_200_OK)
        raise BadgrValidationError("Neither accepted or rejected the direct award", 999)


class DirectAwardDelete(BaseEntityDetailView):
    permission_classes = (AuthenticatedWithVerifiedEmail,)
    http_method_names = ["put"]
    permission_map = {"PUT": "may_award"}

    @extend_schema(
        request=inline_serializer(
            name="DirectAwardDeleteSerializer",
            fields={
                "revocation_reason": serializers.CharField(),
                "direct_awards": serializers.ListField(
                    child=inline_serializer(
                        name="NestedInlineOneOffSerializer",
                        fields={
                            "entity_id": serializers.CharField(),
                        },
                        allow_null=False,
                    )
                ),
            },
        ),
    )
    def put(self, request, **kwargs):
        direct_awards = request.data.get("direct_awards", None)
        revocation_reason = request.data.get("revocation_reason", None)
        if not direct_awards:
            raise BadgrValidationFieldError(
                "direct_awards", "This field is required", 999
            )
        delete_at = datetime.datetime.utcnow() + datetime.timedelta(
            days=settings.DIRECT_AWARDS_DELETION_THRESHOLD_DAYS
        )
        for direct_award in direct_awards:
            direct_award = DirectAward.objects.get(entity_id=direct_award["entity_id"])
            if direct_award.get_permissions(request.user)["may_award"]:
                direct_award.delete_at = delete_at
                direct_award.status = DirectAward.STATUS_DELETED
                direct_award.revocation_reason = revocation_reason
                direct_award.save()
                direct_award.badgeclass.remove_cached_data(["cached_direct_awards"])
                direct_award.bundle.remove_cached_data(["cached_direct_awards"])
                html_message = EmailMessageMaker.create_direct_award_deleted_email(
                    direct_award
                )
                send_mail(
                    subject="Awarded eduBadge has been deleted",
                    message=None,
                    html_message=html_message,
                    recipient_list=[direct_award.recipient_email],
                )
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="DELETE",
                    direct_award_id=direct_award.entity_id,
                    summary=f"Awarded eduBadge has been deleted with reason {revocation_reason}",
                )
            else:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="DELETE",
                    direct_award_entity_id=direct_award.entity_id,
                    summary="User does not have permission",
                )
                raise BadgrApiException400("You do not have permission", 100)
        return Response({"result": "ok"}, status=status.HTTP_200_OK)
