List of emails in badgr-server and their templates:

notify_earner - sent to an earner when they earn a badge
    * ./breakdown/templates/issuer/email/notify_earner_message.html
    * ./breakdown/templates/issuer/email/notify_earner_message.txt
    * ./breakdown/templates/issuer/email/notify_earner_subject.txt


email_confirmation - sent when a user adds a new email to their account
    * ./breakdown/templates/account/email/base.html
    * ./breakdown/templates/account/email/email_confirmation_message.html
    * ./breakdown/templates/account/email/email_confirmation_subject.txt


email_confirmation_signup - sent when a user first signs up for an account
    * ./breakdown/templates/account/email/base.html
    * ./breakdown/templates/account/email/email_confirmation_signup_message.html
    * ./breakdown/templates/account/email/email_confirmation_signup_subject.txt


password_reset_key - sent when a user clicks "forgot password"
    * ./breakdown/templates/account/email/base.html
    * ./breakdown/templates/account/email/password_reset_key_message.html
    * ./breakdown/templates/account/email/password_reset_key_subject.txt


password_reset_confirmation - sent when a users password changes
    * ./breakdown/templates/account/email/base.html
    * ./breakdown/templates/account/email/password_reset_confirmation_message.html
    * ./breakdown/templates/account/email/password_reset_confirmation_subject.txt


