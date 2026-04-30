from typing import Dict, List


class BaseExtensionValidator:
    """
    Base class for all extension validators.
    Automatically registers subclasses in REGISTRY.
    """

    REGISTRY: Dict[str, "BaseExtensionValidator"] = {}

    extension_key: str | None = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

        if not cls.extension_key:
            return  # allow abstract base classes

        if cls.extension_key in cls.REGISTRY:
            raise ValueError(
                f"Duplicate validator for extension '{cls.extension_key}'"
            )

        cls.REGISTRY[cls.extension_key] = cls()

    def validate(self, data: dict) -> List[str]:
        raise NotImplementedError

    @staticmethod
    def require_field(data: dict, field: str) -> List[str]:
        if field not in data:
            return [f"Missing required field '{field}'"]
        return []

    @staticmethod
    def expect_type(value, expected_type, field: str) -> List[str]:
        if not isinstance(value, expected_type):
            return [
                f"Field '{field}' must be {expected_type}, got {type(value)}"
            ]
        return []


class ECTSExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add an ECTS - European Credit Transfer and Accumulation System - number to a badgeclass object."""
    extension_key = "extensions:ECTSExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "ECTS")
        if errors:
            return errors

        value = data["ECTS"]
        errors += self.expect_type(value, (int, float), "ECTS")

        return errors


class EducationProgramIdentifierExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single string EducationProgramIdentifier to a badgeclass object."""
    extension_key = "extensions:EducationProgramIdentifierExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "EducationProgramIdentifier")
        if errors:
            return errors

        value = data["EducationProgramIdentifier"]
        errors += self.expect_type(value, (int, List), "EducationProgramIdentifier")

        return errors


class EQFExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single number EQF to a badgeclass object."""
    extension_key = "extensions:EQFExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "EQF")
        if errors:
            return errors

        value = data["EQF"]
        errors += self.expect_type(value, (int, float), "EQF")

        return errors


class GradingTableExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single url to a webpage providing the institution Grading Table."""
    extension_key = "extensions:GradingTableExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "GradingTable")
        if errors:
            return errors

        value = data["GradingTable"]
        errors += self.expect_type(value, str, "GradingTable")

        return errors


class InstitutionIdentifierExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single string InstitutionIdentifier to an issuer object."""
    extension_key = "extensions:InstitutionIdentifierExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "InstitutionIdentifier")
        if errors:
            return errors

        value = data["InstitutionIdentifier"]
        errors += self.expect_type(value, str, "InstitutionIdentifier")

        return errors


class InstitutionNameExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single string InstitutionName to an issuer object."""
    extension_key = "extensions:InstitutionNameExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "InstitutionName")
        if errors:
            return errors

        value = data["InstitutionName"]
        errors += self.expect_type(value, str, "InstitutionName")

        return errors


class LanguageExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single string Language to a badgeclass object that represents the language of the course."""
    extension_key = "extensions:LanguageExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "Language")
        if errors:
            return errors

        value = data["Language"]
        errors += self.expect_type(value, str, "Language")

        return errors


class LearningOutcomeExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add a single string LearningOutcome to a badgeclass object."""
    extension_key = "extensions:LearningOutcomeExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "LearningOutcome")
        if errors:
            return errors

        value = data["LearningOutcome"]
        errors += self.expect_type(value, str, "LearningOutcome")

        return errors


class StudyLoadExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add the study load in hours to a badgeclass object."""
    extension_key = "extensions:StudyLoadExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "StudyLoad")
        if errors:
            return errors

        value = data["StudyLoad"]
        errors += self.expect_type(value, (int, float), "StudyLoad")

        return errors


class TimeInvestmentExtensionValidator(BaseExtensionValidator):
    """An extension that allows you to add the time investment, expressed in hours needed to earn that badgeclass object."""
    extension_key = "extensions:TimeInvestmentExtension"

    def validate(self, data):
        errors = []

        errors += self.require_field(data, "TimeInvestment")
        if errors:
            return errors

        value = data["TimeInvestment"]
        errors += self.expect_type(value, (int, float), "TimeInvestment")

        return errors
