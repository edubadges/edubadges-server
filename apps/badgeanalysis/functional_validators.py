
class FunctionalValidatorList():
    """
    A list of validators that can return validators for a certain pairing of scheme_slug and validates_type IRI
    """
    def __init__(self):
        self.validators = []

    def register(self, validator):
        if not isinstance(validator, BadgeFunctionalValidator):
            raise TypeError("The validator was supposed to be a BadgeFunctionalValidator. Got: " + validator)
        self.validators.append(validator)

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


class BadgeFunctionalValidator():
    """
    The second type of validator an open badge scheme may have is a Functional Validator,
    which can make sure badge objects pass more precise tests than schema allow.
    """
    def __init__(self, scheme_slugs, validates_types, description="Functional Badge Validator"):
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

    def __unicode__(self):
        return "<BadgeFunctionalValidator: " + self.description + ">"

    def validate(badge):
        return True
