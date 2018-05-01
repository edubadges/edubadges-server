from rest_framework.routers import DefaultRouter

from lti_edu.views import LtiViewSet

router = DefaultRouter()
router.register(r'lti', LtiViewSet, base_name='lti')
urlpatterns = router.urls
