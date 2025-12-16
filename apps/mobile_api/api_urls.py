from django.urls import path

from backpack.api import BackpackAssertionDetail
from badgeuser.api import AcceptTermsView
from directaward.api import DirectAwardAccept
from lti_edu.api import StudentsEnrolledList
from mobile_api.api import BadgeInstances, BadgeInstanceDetail, UnclaimedDirectAwards, Enrollments, EnrollmentDetail, \
    BadgeCollectionsListView, BadgeCollectionsDetailView, Login, AcceptGeneralTerms, DirectAwardDetail

urlpatterns = [
    path('accept-general-terms', AcceptGeneralTerms.as_view(), name='mobile_api_accept_general_terms'),
    path('badge-collections', BadgeCollectionsListView.as_view(), name='mobile_api_badge_collections'),
    path('badge-collections/<str:entity_id>', BadgeCollectionsDetailView.as_view(),
         name='mobile_api_badge_collection_update'),
    path('badge-instances', BadgeInstances.as_view(), name='mobile_api_badge_instances'),
    path('badge-instances/<str:entity_id>', BadgeInstanceDetail.as_view(),
         name='mobile_api_badge_instance_detail'),
    path('badge-instances/<str:entity_id>', BackpackAssertionDetail.as_view(), name='mobile_api_badge_instance_udate'),
    path('direct-awards', UnclaimedDirectAwards.as_view(), name='mobile_api_direct_awards'),
    path('direct-awards/<str:entity_id>', DirectAwardDetail.as_view(), name='mobile_api_direct_awards_detail'),
    path('direct-awards-accept/<str:entity_id>', DirectAwardAccept.as_view(), name='direct_award_accept'),
    path('enrollments', Enrollments.as_view(), name='mobile_api_enrollments'),
    path('enrollments/<str:entity_id>', EnrollmentDetail.as_view(), name='mobile_api_enrollment_detail'),
    path('login', Login.as_view(), name='mobile_api_login'),
    path('terms/accept', AcceptTermsView.as_view(), name='mobile_api_user_terms_accept'),
    path('enroll', StudentsEnrolledList.as_view(), name='mobile_api_lti_edu_enroll_student'),

]
