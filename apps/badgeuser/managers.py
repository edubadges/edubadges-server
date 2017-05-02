from allauth.account.managers import EmailAddressManager
from django.contrib.auth.models import UserManager
from django.core.exceptions import ValidationError


class BadgeUserManager(UserManager):
    duplicate_email_error = 'Account could not be created. An account with this email address may already exist.'

    def create(self,
               email,
               first_name,
               last_name,
               plaintext_password=None,
               send_confirmation=True,
               create_email_address=True):
        from badgeuser.models import CachedEmailAddress

        # If an unverified email record exists that matches this email address, remove it
        try:
            existing_email = CachedEmailAddress.cached.get(email=email)
        except CachedEmailAddress.DoesNotExist:
            pass
        else:
            if existing_email.verified:
                raise ValidationError(self.duplicate_email_error)
            else:
                existing_email.delete()

        # does this email belong to an existing user?
        try:
            existing_user = self.get(email=email)
        except self.model.DoesNotExist:
            # no, create a new user record
            user = self.model(email=email)
        else:
            if existing_user.password:
                # yes, you can't have it
                raise ValidationError(self.duplicate_email_error)
            else:
                # user is claiming an auto-created account
                user = existing_user

        user.first_name = first_name
        user.last_name = last_name
        if plaintext_password:
            user.set_password(plaintext_password)
        user.save()

        # create email address record as needed
        if create_email_address:
            CachedEmailAddress.objects.add_email(user, email, signup=True, confirm=send_confirmation)
        return user


class CachedEmailAddressManager(EmailAddressManager):
    def add_email(self, user, email, request=None, confirm=False, signup=False):
        try:
            email_address = self.get(user=user, email__iexact=email)
        except self.model.DoesNotExist:
            email_address = self.create(user=user, email=email)
            if confirm:
                email_address.send_confirmation(request=request,
                                                signup=signup)

        # Add variant if it does not exist
        if email_address.email.lower() == email.lower() and email_address.email != email:
            self.model.add_variant(email)

        return email_address