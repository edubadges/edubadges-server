from django.db import models


class BadgeClassUserNotification(models.Model):  # noqa: DJ008
    badgeclass = models.ForeignKey("issuer.BadgeClass", blank=False, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey("badgeuser.BadgeUser", blank=False, null=False, on_delete=models.CASCADE)
