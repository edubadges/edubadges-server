from django.urls import path

from endorsement.api import EndorsementList, EndorsementDetail, EndorsementResend

urlpatterns = [
    path("create", EndorsementList.as_view(), name="endorsement_list"),
    path("edit/<str:entity_id>", EndorsementDetail.as_view(), name="endorsement_edit"),
    path("delete/<str:entity_id>", EndorsementDetail.as_view(), name="endorsement_delete"),
    path("resend/<str:entity_id>", EndorsementResend.as_view(), name="endorsement_resend"),
]
