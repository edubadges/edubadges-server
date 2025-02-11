import datetime
import threading

from django.core.exceptions import BadRequest
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
)
from mainsite.permissions import AuthenticatedWithVerifiedEmail
from mainsite.utils import EmailMessageMaker, send_mail
from staff.permissions import HasObjectPermission


def direct_award_remove_cache(direct_award):
    direct_award.bundle.remove_cached_data(["cached_direct_awards"])
    direct_award.badgeclass.remove_cached_data(["cached_direct_awards"])
    direct_award.badgeclass.remove_cached_data(["cached_direct_award_bundles"])


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
            user = badge_instance.user
            return {
                "full_name": user.full_name,
                "email": user.email,
                "public": badge_instance.public,
                "revoked": badge_instance.revoked,
                "entity_id": badge_instance.entity_id,
                "eppn": user.eppns[0] if user.eppns else []
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
                convert_badge_assertion(ba) for ba in award_bundle.badgeinstance_set.all()
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
        un_successful_direct_awards = []
        successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award["entity_id"])
                if not direct_award_db.get_permissions(request.user)["may_award"]:
                    raise BadgrValidationError("No permissions", 100)
                direct_award_db.revoke(revocation_reason)
                successful_direct_awards.append(direct_award_db)
                direct_award_remove_cache(direct_award_db)
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="REVOKE",
                    direct_award_id=direct_award_db.entity_id,
                    summary=f"Directaward revoked with reason {revocation_reason}",
                )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="REVOKE",
                    direct_award_id=direct_award["entity_id"],
                    summary=f"Direct award not revoked, error: {str(e)}",
                )
                un_successful_direct_awards.append(
                    {"error": str(e), "eppn": direct_award.get("eppn"), "email": direct_award.get("recipient_email")})
        if not successful_direct_awards:
            raise BadRequest(
                f"No valid DirectAwards are revoked. All of them were rejected: "
                f"{str(un_successful_direct_awards)}")
        return Response({"result": "ok", "un_successful_direct_awards": un_successful_direct_awards},
                        status=status.HTTP_200_OK)


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
        un_successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award["entity_id"])
                if not direct_award_db.get_permissions(request.user)["may_award"]:
                    raise BadgrValidationError("No permissions", 100)
                direct_award_db.resend_at = datetime.datetime.now()
                direct_award_db.save()
                direct_award_remove_cache(direct_award_db)
                successful_direct_awards.append(direct_award_db)
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="RESEND",
                    direct_award_id=direct_award_db.entity_id,
                    summary="Directaward resent",
                )
            except Exception as e:
                un_successful_direct_awards.append(
                    {"error": str(e), "eppn": direct_award.get("eppn"), "email": direct_award.get("recipient_email")})

        if not successful_direct_awards:
            raise BadRequest(
                f"No valid DirectAwards are resend. All of them were rejected: "
                f"{str(un_successful_direct_awards)}")

        def resend_mails(awards):
            for da in awards:
                da.notify_recipient()

        thread = threading.Thread(target=resend_mails, args=(successful_direct_awards,))
        thread.start()

        return Response({"result": "ok", "un_successful_direct_awards": un_successful_direct_awards},
                        status=status.HTTP_200_OK)


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
        direct_award = self.get_object(request, **kwargs)
        if not self.has_object_permissions(request, direct_award):
            return Response(status=status.HTTP_404_NOT_FOUND)
        if request.data.get("accept", False):  # has accepted it
            if not direct_award.badgeclass.terms_accepted(request.user):
                raise BadgrValidationError(
                    "Cannot accept direct award, must accept badgeclass terms first",
                    999,
                )
            try:
                assertion = direct_award.award(recipient=request.user)
            except BadgrValidationError as err:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="ACCEPT",
                    direct_award_id=direct_award.entity_id,
                    summary="Cannot award as eppn does not match or not member of institution",
                )
                raise err
            direct_award_remove_cache(direct_award)
            direct_award.delete()
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method="ACCEPT",
                direct_award_id=direct_award.entity_id,
                summary="Accepted directaward",
            )
            return Response(
                {"entity_id": assertion.entity_id}, status=status.HTTP_201_CREATED
            )
        elif not request.data.get("accept", True):  # has rejected it
            direct_award.status = DirectAward.STATUS_REJECTED  # reject it
            direct_award.save()
            direct_award_remove_cache(direct_award)
            audit_trail_signal.send(
                sender=request.user.__class__,
                request=request,
                user=request.user,
                method="ACCEPT",
                direct_award_id=direct_award.entity_id,
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
        un_successful_direct_awards = []
        successful_direct_awards = []
        for direct_award in direct_awards:
            try:
                direct_award_db = DirectAward.objects.get(entity_id=direct_award["entity_id"])
                if not direct_award_db.get_permissions(request.user)["may_award"]:
                    raise BadgrValidationError("No permissions", 100)
                if direct_award_db.status == DirectAward.STATUS_DELETED:
                    un_successful_direct_awards.append(
                        {"error": "DirectAward has already been deleted", "eppn": direct_award_db.eppn,
                         "email": direct_award_db.recipient_email})
                else:
                    direct_award_db.delete_at = delete_at
                    direct_award_db.status = DirectAward.STATUS_DELETED
                    direct_award_db.revocation_reason = revocation_reason
                    direct_award_db.save()
                    successful_direct_awards.append(direct_award_db)
                    direct_award_remove_cache(direct_award_db)
                    html_message = EmailMessageMaker.create_direct_award_deleted_email(
                        direct_award_db
                    )
                    send_mail(
                        subject="Awarded eduBadge has been deleted",
                        message=None,
                        html_message=html_message,
                        recipient_list=[direct_award_db.recipient_email],
                    )
                    audit_trail_signal.send(
                        sender=request.user.__class__,
                        request=request,
                        user=request.user,
                        method="DELETE",
                        direct_award_id=direct_award_db.entity_id,
                        summary=f"Awarded eduBadge has been deleted with reason {revocation_reason}",
                    )
            except Exception as e:
                audit_trail_signal.send(
                    sender=request.user.__class__,
                    request=request,
                    user=request.user,
                    method="DELETE",
                    direct_award_entity_id=direct_award["entity_id"],
                    summary=f"{e}",
                )
                un_successful_direct_awards.append(
                    {"error": str(e), "eppn": direct_award.get("eppn"), "email": direct_award.get("recipient_email")})
        if not successful_direct_awards:
            raise BadRequest(
                f"No valid DirectAwards are deleted. All of them were rejected: "
                f"{str(un_successful_direct_awards)}")
        return Response({"result": "ok", "un_successful_direct_awards": un_successful_direct_awards},
                        status=status.HTTP_200_OK)
