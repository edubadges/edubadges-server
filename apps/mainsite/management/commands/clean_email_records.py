from smtplib import SMTPException

from allauth.account.models import EmailConfirmation
from badgeuser.models import BadgeUser, CachedEmailAddress
from django.core.management.base import BaseCommand
from django.db import IntegrityError


class Command(BaseCommand):
    args = ''
    help = 'Ensures users have the proper EmailAddress objects created for their accounts'

    def handle(self, *args, **options):
        users_processed = 0
        primaries_set = 0
        email_errors = 0
        user_errors = 0

        for user in BadgeUser.objects.all():
            users_processed += 1
            try:
                emails = CachedEmailAddress.objects.filter(user=user)

                # handle users who don't have an EmailAddress record
                if emails.count() < 1:
                    try:
                        existing_email = CachedEmailAddress.objects.get(email=user.email)
                    except CachedEmailAddress.DoesNotExist:
                        new_primary = CachedEmailAddress(
                            user=user, email=user.email, verified=False, primary=True
                        )
                        new_primary.save()
                        new_primary.send_confirmation(signup="canvas")
                    else:
                        user.delete()  # User record has no email addresses and email address has been added under another account
                        continue

                    emails = CachedEmailAddress.objects.filter(user=user)

                # User has emails but none marked primary
                elif len([e for e in emails if e.primary is True]) == 0:
                    new_primary = emails.first()
                    new_primary.set_as_primary(conditional=True)
                    self.stdout.write("Set {} as primary for user {}".format(new_primary.email, user.pk))
                    primaries_set += 1

                    prior_confirmations = EmailConfirmation.objects.filter(email_address=new_primary)

                    if new_primary.verified is False and not prior_confirmations.exists():
                        try:
                            new_primary.send_confirmation(signup="canvas")
                        except SMTPException as e:
                            raise e
                        except Exception as e:
                            raise SMTPException("Error sending mail to {} -- {}".format(
                                new_primary.email, e.message
                            ))
            except IntegrityError as e:
                user_errors += 1
                self.stdout.write("Error in user {} record: {}".format(user.pk, e.message))
                continue
            except SMTPException as e:
                email_errors += 1
                self.stdout.write("Could not send mail: {}".format(e.message))

        self.stdout.write(
            "Done cleaning email: {} users, {} updated primaries, {} user errors, {} email errors.".format(
                users_processed, primaries_set, user_errors, email_errors
            )
        )