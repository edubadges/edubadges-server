

"""
Classes for the validation results from schema and functional validators. 
These will be stored in a JSONField array, so they should be JSON-serializable formats,
objects.
"""
class BadgeValidationMessage():
    message_type = "message"

    def __init__(self, message_string, validator_string):
        if not isinstance(message_string, (str, unicode)):
            raise TypeError("Can't add " + self.message_type + " to Open Badge. Not of type string: " + message_string)
        self.message_content = message_string

        if not isinstance(message_string, (str, unicode)):
            raise TypeError("Validator string should be of type string: " + validator_string)
        self.validator = validator_string

    def __unicode__(self):
        return "<Badge Validation " + self.message_type + ": " + self.message_content + ">"


class BadgeValidationSuccess(BadgeValidationMessage):
    message_type = "success"


class BadgeValidationError(BadgeValidationMessage):
    message_type = "error"
