from allauth.account.managers import EmailAddressManager


class CachedEmailAddressManager(EmailAddressManager):
    def add_email(self, request, user, email, confirm=False, signup=False):
        try:
            email_address = self.get(user=user, email__iexact=email)
        except self.model.DoesNotExist:
            email_address = self.create(user=user, email=email)
            if confirm:
                email_address.send_confirmation(request,
                                                signup=signup)

        # Add variant if it does not exist
        if email_address.email.lower() == email.lower() and email_address.email != email:
            self.model.add_variant(email)

        return email_address