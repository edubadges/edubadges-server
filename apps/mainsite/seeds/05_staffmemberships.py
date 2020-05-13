from django.conf import settings

from badgeuser.models import BadgeUser
from issuer.models import BadgeClass

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
