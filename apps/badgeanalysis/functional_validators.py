from validation_messages import BadgeValidationSuccess, BadgeValidationError
from django.conf import settings
from django.utils.importlib import import_module


class FunctionalValidatorList():
    """
    A list of validators that can return validators for a certain pairing of scheme_slug and validates_type IRI
    """
    def __init__(self):
        self.validators = []
        self.register_default_validators()

    def register(self, validator):
        if not isinstance(validator, BadgeFunctionalValidator):
            raise TypeError("The validator was supposed to be a BadgeFunctionalValidator. Got: " + validator)
        if self.find_by_slug(validator.slug) is not None:
            raise TypeError("Duplicate Validator already exists with this slug: " + validator.slug)
        self.validators.append(validator)

    def register_default_validators(self):
        self.register(AssertionRecipientValidator())

    def find_by_slug(self, slug):
        for validator in self.validators:
            if validator.slug == slug:
                return validator
        return None

    def validators_for(self, scheme_slug, validates_type):
        if not isinstance(scheme_slug, (str, unicode)) or not isinstance(validates_type, (str, unicode)):
            return None

        def validator_match(validator):
            if scheme_slug in validator.scheme_slug and validates_type in validator.validates_type:
                return True
            return False

        success_list = []
        for validator in self.validators:
            if validator_match(validator):
                success_list.append(validator)

        return success_list


def get_current_validator_list():
    list_cls = getattr(settings, 'BADGEANALYSIS_VALIDATOR_LIST', None)
    if list_cls:
        try:
            mod, inst = list_cls.rsplit('.', 1)
            mod = import_module(mod)
            validator_list = getattr(mod, inst)()
        except:
            validator_list = FunctionalValidatorList()
    else:
        validator_list = FunctionalValidatorList()
    return validator_list


class BadgeFunctionalValidator():
    """
    The second type of validator an open badge scheme may have is a Functional Validator,
    which can make sure badge objects pass more precise tests than schema allow.
    """
    def __init__(self, scheme_slugs, validates_types, slug, description="Functional Badge Validator"):
        def validate_str_or_list(entry):
            if isinstance(entry, (str, unicode)):
                return [entry]
            if isinstance(entry, (list, set)):
                for item in entry:
                    if not isinstance(item, (str, unicode)):
                        raise TypeError("Inappropriate item in list: " + item)
                return entry
            else:
                raise TypeError("Unknown type of input: " + entry)

        self.scheme_slug = validate_str_or_list(scheme_slugs)
        self.validates_type = validate_str_or_list(validates_types)

        if not isinstance(description, (str, unicode)):
            raise TypeError("Description should be a string. Got: " + description)
        self.description = description

        if not isinstance(slug, (str, unicode)):
            raise TypeError("Slug should be a string. Got: " + slug)
        self.slug = slug

    def __unicode__(self):
        return "<BadgeFunctionalValidator %s: %s >" % (self.slug, self.description)

    def validate(self, badge):
        return BadgeValidationSuccess("No validation function implemented, so we'll call it good.", self.__unicode__())


class AssertionRecipientValidator(BadgeFunctionalValidator):
    def __init__(self):
        super(AssertionRecipientValidator)

    def validate(self, badge):
        if badge.scheme.slug in ('1_0', '1_1'):
            identity_string = badge.getLd('asn', 'recipient')

    def verify_recipient(identity_string, hash_string, salt):
        """
        Check if a badge recipient is indeed the expected recipient (email address)
        """
        if hash_string.startswith('sha256$'):
            return hash_string == 'sha256$' + hashlib.sha256(email+salt).hexdigest()
        elif hash_string.startswith('md5$'):
            return hash_string == 'md5$' + hashlib.md5(email+salt).hexdigest()

