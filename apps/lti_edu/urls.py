from lti_edu.views import LtiViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'lti', LtiViewSet, base_name='lti')
urlpatterns = router.urls
