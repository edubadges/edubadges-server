import badgrlog


badgrlogger = badgrlog.BadgrLogger()

def log_user_signed_up(sender, **kwargs):
    badgrlogger.event(badgrlog.UserSignedUp(**kwargs))

def log_email_confirmed(sender, **kwargs):
    badgrlogger.event(badgrlog.EmailConfirmed(**kwargs))
