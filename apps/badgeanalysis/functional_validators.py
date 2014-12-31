from validation_messages import BadgeValidationSuccess, BadgeValidationError, BadgeValidationMessage
from django.conf import settings
from django.utils.importlib import import_module
import hashlib


class FunctionalValidatorList(object):
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
        pass

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

# Gets a custom validator list from settings or instantiates a default.

def get_current_validator_list():
    try:
        if isinstance(current_validator_list, FunctionalValidatorList):
            return current_validator_list
    except NameError:
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

current_validator_list = get_current_validator_list()

class BadgeFunctionalValidator(object):
    """
    The second type of validator an open badge scheme may have is a Functional Validator,
    which can make sure badges pass more precise tests than schema allow.
    """
    def __init__(self, **kwargs):
        # Pass in these kwargs:
        scheme_slugs = kwargs.get('scheme_slugs')
        validates_types = kwargs.get('validates_types')
        slug = kwargs.get('slug')
        description = kwargs.get('description', "Functional Badge Validator")
        validation_function = kwargs.get('validation_function')

        def accept_str_or_list(entry):
            if isinstance(entry, (str, unicode)):
                return [entry]
            if isinstance(entry, (list, set)):
                for item in entry:
                    if not isinstance(item, (str, unicode)):
                        raise TypeError("Inappropriate item in list: " + item)
                return entry
            else:
                raise TypeError("Unknown type of input: " + entry)

        self.scheme_slug = accept_str_or_list(scheme_slugs)
        self.validates_type = accept_str_or_list(validates_types)

        if not isinstance(description, (str, unicode)):
            raise TypeError("Description should be a string. Got: " + description)
        self.description = description

        if not isinstance(slug, (str, unicode)):
            raise TypeError("Slug should be a string. Got: " + slug)
        self.slug = slug

        if not hasattr(validation_function, '__call__'):
            raise TypeError("Validation_method should be a function. Got: " + validation_function)
        self.validate = validation_function

    def __unicode__(self):
        return "BadgeFunctionalValidator %s: %s" % (self.slug, self.description)

    """
    Follow this function signature to validate an Open Badge.
    Return a BadgeValidationSuccess, BadgeValidationError or BadgeValidationMessage
    (badge is expected to be an OpenBadge)
    """
    # def validate(self, badge):
       # return BadgeValidationSuccess("No validation function implemented, so we'll call it good.", self.__unicode__())


class BadgeObjectFunctionalValidator(object):
    """
    A validator just for badge objects at the processBadgeObject stage. These validators cannot rely on 
    methods of OpenBadge instances. Their validate method takes a badgeMetaObject as input and returns either a
    BadgeValidationSuccess (positive), BadgeValidationMessage (neutral) or BadgeValidationError (negative)
    """
    def __init__(self, **kwargs):
        # TODO test these inputs to make sure slug is a string and validation method is a method
        self.slug = kwargs.get('slug')
        self.validate = kwargs.get('validation_function')

    def __unicode__(self):
        return "Functional:%s" % (self.slug)


"""
A BadgeObjectFunctionalValidator that determines if the badge recipient is the one the user expected.
"""
def assertion_recipient_validator_function(self, badgeMetaObject):
    def verify_recipient(identity_string, hash_string, salt=''):
        """
        Check if a badge recipient is indeed the expected recipient (email address)
        """
        if hash_string.startswith('sha256$'):
            return hash_string == 'sha256$' + hashlib.sha256(identity_string+salt).hexdigest()
        elif hash_string.startswith('md5$'):
            return hash_string == 'md5$' + hashlib.md5(identity_string+salt).hexdigest()
        else:
            return hash_string == identity_string

    if badgeMetaObject['scheme'].slug in ('1_0', '1_1', '1_0-backpack-misbaked'):
        hash_string = badgeMetaObject['badgeObject'].get('recipient').get('identity')
        salt = badgeMetaObject['badgeObject'].get('recipient').get('salt', '')
    elif badgeMetaObject['scheme'].slug in ('0_5'):
        hash_string = badgeMetaObject['badgeObject'].get('recipient')
        salt = badgeMetaObject['badgeObject'].get('salt','')

    recipient_input = badgeMetaObject['recipient_input']

    if verify_recipient(recipient_input, hash_string, salt):
        return BadgeValidationSuccess(
            "Provided recipient identity string matched assertion recipient.",
            self.__unicode__()
        )
    else:
        return BadgeValidationError(
            "Recipient input %s didn't match hashed string: %s" % (recipient_input, hash_string),
            self.__unicode__()
        )

assertionRecipientValidator = BadgeObjectFunctionalValidator(**{
    'slug': 'AssertionRecipientValidator',
    'validation_function': assertion_recipient_validator_function,
    'scheme_slugs': ['0_5', '1_0', '1_1', '1_0-backpack-misbaked'],
    'validates_types': ['assertion']
})
