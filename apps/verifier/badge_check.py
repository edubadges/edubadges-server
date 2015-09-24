import inspect

from rest_framework.serializers import ValidationError

from composition.utils import badge_email_matches_emails

from .utils import domain


class BadgeCheckBase(object):
    warnings = []

    def __new__(cls, badge_instance, *args, **kwargs):
        if badge_instance.version.startswith('v1'):
            cls = BadgeCheckTests_V1_0
        if badge_instance.version.startswith('v0'):
            cls = BadgeCheckTests_V0_5

        return super(BadgeCheckBase, cls).__new__(cls, badge_instance,
                                                  *args, **kwargs)

    def __init__(self, badge_instance, badge_class, issuer,
                 verified_emails, badge_instance_url=None):
        self.badge_instance = badge_instance
        self.badge_class = badge_class
        self.issuer = issuer
        self.verified_emails = verified_emails
        self.instance_url = badge_instance_url

    def validate(self):
        self.results = []

        checks = inspect.getmembers(
            self, lambda method: inspect.ismethod(method)
            and method.__name__.startswith('check_'))

        for check_name, check_method in checks:
            check_type = check_name in self.warnings and 'warning' or 'error'
            try:
                success_message = getattr(self, check_name)()
                self.results.append({
                    "name": check_name, "success": True,
                    "type": check_type, "message": success_message})
            except ValidationError as e:
                self.results.append({
                    "name": check_name, "success": False,
                    "type": check_type, "message": e.detail})

        return self.is_valid()

    def is_valid(self):
        if not self.results:
            self.validate()

        for result in self.results:
            if result['type'] == 'error' and not result['success']:
                return False

        return True


class BadgeCheck(BadgeCheckBase):

    def __init__(self, *args, **kwargs):
        self.recipient_id = None
        super(BadgeCheck, self).__init__(*args, **kwargs)

    def validate(self):
        self.recipient_id = None
        super(BadgeCheck, self).validate()

    def check_components_have_same_version(self):
        # Validation between components of the MetaSerializer
        same_version_components = (self.badge_class.version ==
                                   self.issuer.version ==
                                   self.badge_instance.version)
        if not same_version_components:
            raise ValidationError(
                "Components assembled with different specification versions.")

        return "All components of the Open Badge were properly structured, and \
            their versions are compatible: '{}'".format(
                self.badge_instance.version)

    def check_badge_belongs_to_recipient(self):
        # Request.user specific validation
        recipient_id = badge_email_matches_emails(self.badge_instance,
                                                   self.verified_emails)
        if not recipient_id:
            raise ValidationError(
                "The badge you are trying to import does not belong to one of \
                your verified e-mail addresses.")

        self.recipient_id = recipient_id

        return "The badge was issued to '{}' as expected".format(recipient_id);


class BadgeCheckTests_V0_5(BadgeCheck):

    def __init__(self, *args, **kwargs):
        super(BadgeCheckTests_V0_5, self).__init__(*args, **kwargs)
        self.warnings.extend(
            ['check_issuing_platform_domain_against_assertion_host'])

    def validate(self):
        # Form-specific badge instance validation (reliance on URL input)
        if not self.instance_url:
            raise ValidationError(
                "We cannot verify a v0.5 badge without its hosted URL.")

        super(BadgeCheckTests_V0_5, self).validate()

    def check_issuing_platform_domain_against_assertion_host(self):
        # Form-specific badge instance validation (reliance on form data)
        if not (domain(self.issuer['origin']) ==
                domain(self.instance_url)):  # TODO: Can come from baked image
            raise ValidationError(
                "The URL of the institution does not match the verifiable \
                host of the assertion, and authorized use of a remote platform \
                could not be verified.")

        return "This badge was issued from a platform on the issuer's domain."


class BadgeCheckTests_V1_0(BadgeCheck):

    def __init__(self, *args, **kwargs):
        super(BadgeCheckTests_V1_0, self).__init__(*args, **kwargs)
        self.warnings.extend(
            ['check_issuing_platform_domain_against_assertion_host'])

    def check_components_have_same_domain(self):
        resources = filter(None, [self.badge_instance['verify']['url'],
                                  self.badge_instance['badge'],
                                  self.badge_instance.get('url'),
                                  self.badge_instance.get('id')])
        same_domains = len(set([domain(resource)
                                for resource in resources])) == 1
        if not same_domains:
            raise ValidationError(
                "Badge components are not all hosted on the same domain, \
                which indicates a counterfeit badge.")

        return "Badge components are properly hosted on the same domain."

    def check_issuing_platform_domain_against_assertion_host(self):
        # Form-specific badge instance validation (reliance on form data)
        if not (domain(self.issuer['url']) ==
                domain(self.instance_url)):  # TODO: Can come from baked image
            raise ValidationError(
                "The URL of the institution does not match the verifiable \
                host of the assertion, and authorized use of a remote platform \
                could not be verified.")

        return "This badge was issued from a platform on the issuer's domain."
