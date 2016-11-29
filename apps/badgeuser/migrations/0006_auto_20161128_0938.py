# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations, IntegrityError, transaction
from allauth.account.adapter import get_adapter
from allauth.account.models import EmailConfirmation

from badgeuser.models import CachedEmailAddress, BadgeUser


def send_missing_confirmation_requests(apps, schema_editor):
    """
    1. Detect all users who do do not have a Primary Email Address
    2. Find first email address, set is as primary.
    3. send verification email for that address.
    """
    for user in BadgeUser.objects.all():
        with transaction.atomic():
            emails = CachedEmailAddress.objects.filter(user=user)
            # record users who don't have EmailAddress records
            if emails.count() < 1:
                try:
                    new_primary = CachedEmailAddress(
                        user=user, email=user.email, verified=False, primary=True
                    )
                    new_primary.save()
                    emails = CachedEmailAddress.objects.filter(user=user)
                except IntegrityError:
                    continue

            elif len([e for e in emails if e.primary is True]) == 0:
                new_primary = emails.first()
                new_primary.set_as_primary(conditional=True)
                if new_primary.verified is False:
                    new_primary.send_confirmation()


class Migration(migrations.Migration):

    dependencies = [
        ('badgeuser', '0005_auto_20160901_1537'),
    ]

    operations = [
        migrations.RunPython(send_missing_confirmation_requests)
    ]
