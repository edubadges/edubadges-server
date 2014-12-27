

"""
Classes for the validation results from schema and functional validators. 
These will be stored in a JSONField array, so they should be JSON-serializable formats,
objects.

example:
badge_validation_message = BadgeValidationError("Recipient ID is hashed and no recipient_input provided", "RecipientRequiredValidator")
"""


class BadgeValidationMessage(Exception):
    message_type = "message"

    def __init__(self, message_string, validator_string):
        if not isinstance(message_string, (str, unicode)):
            message_string = "Can't add " + self.message_type + " to Open Badge. Not of type string: " + message_string

        if not isinstance(validator_string, (str, unicode)):
            validator_string = "Validator string should be of type string: " + validator_string

        # Call the base class constructor with the parameters it needs
        super(BadgeValidationMessage, self).__init__(
            "<Badge Validation " + self.message_type
            + " (" + validator_string + "): " + message_string + ">"
        )


class BadgeValidationSuccess(BadgeValidationMessage):
    message_type = "success"


class BadgeValidationError(BadgeValidationMessage):
    message_type = "error"
