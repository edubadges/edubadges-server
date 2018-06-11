from allauth.account.managers import EmailAddressManager
from django.contrib.auth.models import UserManager
from django.core.exceptions import ValidationError

from mainsite.models import BadgrApp


class BadgeUserManager(UserManager):
    duplicate_email_error = 'Account could not be created. An account with this email address may already exist.'

    def create(self,
               email,
               first_name,
               last_name,
               request=None,
               plaintext_password=None,
               send_confirmation=True,
               create_email_address=True,
               marketing_opt_in=False
               ):
        from badgeuser.models import CachedEmailAddress, TermsVersion

        user = None

        # Do we know about this email address yet?
        try:
            existing_email = CachedEmailAddress.cached.get(email=email)
        except CachedEmailAddress.DoesNotExist:
            # nope
            pass
        else:
            if not existing_email.user.password:
                # yes, its owned by an auto-created user trying to set a password
                user = existing_email.user
            elif existing_email.verified:
                raise ValidationError(self.duplicate_email_error)
            else:
                # yes, its an unverified email address owned by a claimed user
                # remove the email
                existing_email.delete()
                # if the user no longer has any emails, remove it
                if len(existing_email.user.cached_emails()) == 0:
                    existing_email.user.delete()

        badgrapp = BadgrApp.objects.get_current(request=request)

        if user is None:
            user = self.model(email=email)

        user.first_name = first_name
        user.last_name = last_name
        user.badgrapp = badgrapp
        user.marketing_opt_in = marketing_opt_in
        user.agreed_terms_version = TermsVersion.cached.cached_latest_version()
        if plaintext_password:
            user.set_password(plaintext_password)
        user.save()

        # create email address record as needed
        if create_email_address:
            CachedEmailAddress.objects.add_email(user, email, request=request, signup=True, confirm=send_confirmation)
        return user


class CachedEmailAddressManager(EmailAddressManager):
    def add_email(self, user, email, request=None, confirm=False, signup=False):
        try:
            email_address = self.get(user=user, email__iexact=email)
        except self.model.DoesNotExist:
            email_address = self.create(user=user, email=email)
        if confirm and not email_address.verified:
            email_address.send_confirmation(request=request, signup=signup)

        # Add variant if it does not exist
        if email_address.email.lower() == email.lower() and email_address.email != email:
            self.model.add_variant(email)

        return email_address