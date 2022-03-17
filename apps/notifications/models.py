from django.db import models


class BadgeClassUserNotification(models.Model):
    badgeclass = models.ForeignKey('issuer.BadgeClass', blank=False, null=False, on_delete=models.CASCADE)
    user = models.ForeignKey('badgeuser.BadgeUser', blank=False, null=False, on_delete=models.CASCADE)
