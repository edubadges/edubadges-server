from rest_framework import routers
from badgeanalysis.api import BadgeViewSet

# Django REST Framework router
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'badges', BadgeViewSet)
