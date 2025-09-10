from django.urls import path

from mobile_api.api import BadgeInstances, BadgeInstanceDetail, UnclaimedDirectAwards, Enrollments, EnrollmentDetail, \
    BadgeCollectionsListView, BadgeCollectionsDetailView, Login, AcceptGeneralTerms

urlpatterns = [
    path('accept-general-terms', AcceptGeneralTerms.as_view(), name='mobile_api_accept_general_terms'),
    path('badge-collections', BadgeCollectionsListView.as_view(), name='mobile_api_badge_collections'),
    path('badge-collections/<str:entity_id>', BadgeCollectionsDetailView.as_view(),
         name='mobile_api_badge_collection_update'),
    path('badge-instances', BadgeInstances.as_view(), name='mobile_api_badge_instances'),
    path('badge-instances/<str:entity_id>', BadgeInstanceDetail.as_view(),
         name='mobile_api_badge_instance_detail'),
    path('direct-awards', UnclaimedDirectAwards.as_view(), name='mobile_api_direct_awards'),
    path('enrollments', Enrollments.as_view(), name='mobile_api_enrollments'),
    path('enrollments/<str:entity_id>', EnrollmentDetail.as_view(), name='mobile_api_enrollment_detail'),
    path('login', Login.as_view(), name='mobile_api_login'),

]
