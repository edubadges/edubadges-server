from django.urls import path, include
from rest_framework import routers

from backpack.api import BackpackAssertionDetail
from badgeuser.api import AcceptTermsView
from directaward.api import DirectAwardAccept
from lti_edu.api import StudentsEnrolledList
from mobile_api.api import (
    BadgeInstances,
    BadgeInstanceDetail,
    BadgeClassDetailView,
    UnclaimedDirectAwards,
    Enrollments,
    EnrollmentDetail,
    Login,
    AcceptGeneralTerms,
    DirectAwardDetailView,
    CatalogBadgeClassListView,
    UserProfileView,
    InstitutionListView,
    RegisterDeviceViewSet,
    BadgeCollectionViewSet,
)
from mobile_api.test_api import (
    TestAnalyticsAPI,
    TestRateLimitAPI,
    AnalyticsSummaryAPI,
)


router = routers.DefaultRouter()

router.register(
    'badge-collections',
    BadgeCollectionViewSet,
    basename='badge-collections',
)

urlpatterns = [
    path('accept-general-terms', AcceptGeneralTerms.as_view(), name='mobile_api_accept_general_terms'),
    path('badge-classes/<str:entity_id>', BadgeClassDetailView.as_view(), name='mobile_api_badge_class_detail'),
    path('badge-instances', BadgeInstances.as_view(), name='mobile_api_badge_instances'),
    path('badge-instances/<str:entity_id>', BadgeInstanceDetail.as_view(), name='mobile_api_badge_instance_detail'),
    path('direct-awards', UnclaimedDirectAwards.as_view(), name='mobile_api_direct_awards'),
    path('direct-awards/<str:entity_id>', DirectAwardDetailView.as_view(), name='mobile_api_direct_awards_detail'),
    path('direct-awards-accept/<str:entity_id>', DirectAwardAccept.as_view(), name='direct_award_accept'),
    path('enrollments', Enrollments.as_view(), name='mobile_api_enrollments'),
    path('enrollments/<str:entity_id>', EnrollmentDetail.as_view(), name='mobile_api_enrollment_detail'),
    path('login', Login.as_view(), name='mobile_api_login'),
    path('badge/public', BackpackAssertionDetail.as_view(), name='mobile_api_badge_public'),
    path('terms/accept', AcceptTermsView.as_view(), name='mobile_api_user_terms_accept'),
    path('enroll', StudentsEnrolledList.as_view(), name='mobile_api_lti_edu_enroll_student'),
    path('profile', UserProfileView.as_view(), name='mobile_api_user_profile'),
    path('catalog', CatalogBadgeClassListView.as_view(), name='mobile_api_catalog_badge_class'),
    path('institutions', InstitutionListView.as_view(), name='mobile_api_institution_list'),
    path('register-device', RegisterDeviceViewSet.as_view({'post': 'create'}), name='mobile_api_register_device'),
    path('', include(router.urls)),
    # Test endpoints for analytics and rate limiting
    path('test-analytics', TestAnalyticsAPI.as_view(), name='mobile_api_test_analytics'),
    path('test-rate-limit', TestRateLimitAPI.as_view(), name='mobile_api_test_rate_limit'),
    path('analytics-summary', AnalyticsSummaryAPI.as_view(), name='mobile_api_analytics_summary'),
]
