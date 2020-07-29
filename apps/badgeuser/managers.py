from allauth.account.managers import EmailAddressManager
from cachemodel.managers import CacheModelManager
from django.contrib.auth.models import UserManager
from mainsite.models import BadgrApp


class BadgeUserManager(UserManager):
    duplicate_email_error = 'Account could not be created. An account with this email address may already exist.'

    def create(self,
               email,
               first_name,
               last_name,
               request=None,
               send_confirmation=True,
               create_email_address=True,
               marketing_opt_in=False
               ):
        from badgeuser.models import CachedEmailAddress

        user = None

        badgrapp = BadgrApp.objects.get_current(request=request)

        if user is None:
            user = self.model(email=email)

        user.first_name = first_name
        user.last_name = last_name
        user.badgrapp = badgrapp
        user.marketing_opt_in = marketing_opt_in
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


class EmailAddressCacheModelManager(CacheModelManager):
    
    def get_student_email(self, email_address):
        from badgeuser.models import CachedEmailAddress
        all_matching_emails = CachedEmailAddress.cached.filter(email=email_address)
        student_email = [email for email in all_matching_emails if email.user.is_student]
        if not student_email:
            raise CachedEmailAddress.DoesNotExist
        if len(student_email) > 1:
            raise CachedEmailAddress.MultipleObjectsReturned
        return student_email[0]
    