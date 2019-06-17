def create_student_badge_request_email(badge_class):
    mail_template = 'Dear student, \n\n ' \
                                    '\tYou have successfully requested the following badge. \n\n' \
                                    '\t{}, {} \n\n' \
                                    '\tPlease wait for the issuer of this badge to accept your request. \n\n' \
                                    'Regards, \n\n' \
                                    'The Edubadges team'
    return mail_template.format(badge_class.name, badge_class.public_url)


def create_issuer_staff_badge_request_email(badge_classes):
    badge_classes_string = ''.join(['\t- {name} (issuer: {issuer})\n\n'.format(issuer=badge_class.issuer.name, name=badge_class.name) for badge_class in badge_classes])
    mail_template = 'Dear staff member, \n\n ' \
                    '\tYou have new badge requests for the following badge class{0}. \n\n' \
                    '{1}' \
                    '\tThese new requests have been made in the last 24 hours. \n\n' \
                    'Regards, \n\n' \
                    'The Edubadges team'
    plural = 'es' if len(badge_classes) > 1 else ''
    return mail_template.format(plural, badge_classes_string)
