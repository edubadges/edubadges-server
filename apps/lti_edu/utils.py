def create_badge_request_email_content(badgeclass):
    badge_requested_mail_template = 'Dear student, \n\n ' \
                                    '\t You have successfully requested the following badge. \n\n' \
                                    '\t{}, {} \n\n' \
                                    '\t Please wait for the issuer of this badge to accept your request. \n\n' \
                                    'Regards, \n\n' \
                                    'The Edubadges team'
    return badge_requested_mail_template.format(badgeclass.name, badgeclass.public_url)