from badgeuser.models import BadgeUser
from django.conf import settings
from mainsite.models import BadgrApp

super_user = BadgeUser.objects.get(username=settings.SUPERUSER_NAME)
badgr_app = BadgrApp.objects.get(id=getattr(settings, 'BADGR_APP_ID'))

# TODO: Use Bers seeding logic