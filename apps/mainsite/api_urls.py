from rest_framework import routers
from badgeanalysis.api import BadgeViewSet
from issuer.api import EarnerNotificationViewSet

# Django REST Framework router
router = routers.DefaultRouter(trailing_slash=False)
router.register(r'badges', BadgeViewSet)
router.register(r'issuer/notifications', EarnerNotificationViewSet)
