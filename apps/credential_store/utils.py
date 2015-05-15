from allauth.account.models import EmailAddress


def find_recipient_user(recipient_id):
    try:
        confirmed_email = EmailAddress.objects.get(
            email=recipient_id, verified=True
        )
    except EmailAddress.ObjectNotFound:
        return None
    else:
        return confirmed_email.user
