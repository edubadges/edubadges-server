# utility methods for analyzing badge objects
# (Assertions, BadgeClasses, IssuerOrgs, and Extensions)
# in general, and for each specific case, allowing us to run the
# appropriate validations and manipulations for each case without
# embedding all that logic in the procedure itself.
from django.db import models
from django.db.models.signals import post_init
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from jsonfield import JSONField
import json
from validation_messages import BadgeValidationSuccess, BadgeValidationError
import badgeanalysis.utils
from scheme_models import BadgeScheme
from badgeanalysis.functional_validators import assertionRecipientValidator
import basic_models

from django.conf import settings
from django.utils.module_loading import import_string


class BadgeObject(basic_models.TimestampedModel):
    CLASS_TYPE = 'unknown'
    iri = models.CharField(max_length=2048)  # Internationalized Resource Identifier
    badge_object = JSONField()
    scheme = models.ForeignKey(BadgeScheme)
    errors = JSONField()
    notes = JSONField()

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        docloader = import_string(getattr(settings, 'REMOTE_DOCUMENT_FETCHER'))
        if not badgeanalysis.utils.test_probable_url(self.iri):
            raise BadgeValidationError("Badge Object input IRI is not a known dereferencable format " + str(self.iri))

        try:
            hosted_badge_object = badgeanalysis.utils.try_json_load(docloader(self.iri))
            self.badge_object = hosted_badge_object
        except:
            raise BadgeValidationError("Could not fetch " + self.CLASS_TYPE + " from " + self.iri)
            return

        try:
            self.scheme = self.validate_object_scheme()
        except BadgeValidationError as e:
            raise e
        else:
            self.augment_badge_object_LD()

    @classmethod
    def get_or_create_by_iri(cls, iri, *args, **kwargs):
        existing_object = cls.detect_existing(iri)
        if existing_object is not None and cls.CLASS_TYPE not in kwargs.get('create_only', ()):
            return existing_object
        elif existing_object is not None:
            raise BadgeValidationError("Badge Object (" + cls.CLASS_TYPE + ") already exists with IRI: " + iri, "create_only", iri)
        else:
            new_object = cls(iri=iri)
            kwargs[iri] = 'new'
            try:
                new_object.save(*args, **kwargs)
            except BadgeValidationError as e:
                raise e
                return
            else:
                return new_object

    @classmethod
    def get_or_create_by_badge_object(cls, badge_input, *args, **kwargs):
        # If we have JSON as a string, try to load it before treating it as a potential URL
        if not isinstance(badge_input, dict):
            badge_input = badgeanalysis.utils.try_json_load(badge_input)

        # If we've got a URL, create this object from the URL.
        if isinstance(badge_input, (str, unicode)):
            if badgeanalysis.utils.test_probable_url(badge_input):
                return cls.get_or_create_by_iri(processed_input, *args, **kwargs)
            else:
                return BadgeValidationError("Did not know how to fetch badge object from " + badge_input, "unreadable URL", badge_input)

        # Else, figure out the hosted assertion URL, then create by that.
        if cls.CLASS_TYPE == 'assertion':
            badge_object_id = badge_input.get('@id', None) or badge_input.get('verify', {}).get('url', None)
            if badge_object_id is not None:
                try:
                    new_object = cls.get_or_create_by_iri(badge_object_id, *args, **kwargs)
                except BadgeValidationError as e:
                    raise e
                    return
                return new_object

        # Cannot create by object unless its an assertion whose id is findable
        raise BadgeValidationError("Cannot create " + cls.CLASS_TYPE + " by object / verification URL not found.")

    @classmethod
    def detect_existing(cls, iri):
        try:
            existing_assertion = cls.objects.get(iri=iri)
        except ObjectDoesNotExist:
            return None
        except MultipleObjectsReturned as e:
            raise e
        else:
            return existing_assertion

    def validate_object_scheme(self):
        context_url = badgeanalysis.utils.validateMainContext(self.badge_object.get('@context', ''))
        if context_url is not None:
            scheme = BadgeScheme.objects.get(slug='1_1')

            val_result = scheme.test_against_schema_for(self.badge_object, self.CLASS_TYPE)
            if isinstance(val_result, str):
                raise BadgeValidationError(self.CLASS_TYPE + " did not validate against schema. " + val_result)
            else:
                return scheme

        legacy_scheme = BadgeScheme.get_legacy_scheme_match(self.badge_object, self.CLASS_TYPE)
        if legacy_scheme is None:
            raise BadgeValidationError("Could not determine type of badge object with known schema set")
        else:
            scheme_result = legacy_scheme.get('scheme', None)
            return scheme_result

    def augment_badge_object_LD(self):
        """ Finalize badge object by adding the @id if possible """
        if '@id' not in self.badge_object:
            self.badge_object['@id'] = self.iri
        if '@type' not in self.badge_object:
            self.badge_object['@type'] = self.CLASS_TYPE
        if '@context' not in self.badge_object:
            self.badge_object['@context'] = self.scheme.context_url


class Assertion(BadgeObject):
    CLASS_TYPE = 'assertion'
    badgeclass = models.ForeignKey('badgeanalysis.BadgeClass', blank=True, null=True)
    # openbadge = related OpenBadge (reverse OneToOneField relationship)

    def save(self, *args, **kwargs):
        # If existing_assertion hasn't already been tested, do that.
        if kwargs.get(self.iri, None) != 'new':
            existing_assertion = Assertion.detect_existing(self.iri)
            if existing_assertion is not None:
                return existing_assertion

        # TODO: What kind of exceptions might be raised here? Anything worth handling?
        try:
            super(Assertion, self).save(*args, **kwargs)
        except BadgeValidationError as e:
            raise e
            return

        badgeclass_iri = self.badge_object.get('badge')
        self.badgeclass = BadgeClass.get_or_create_by_iri(badgeclass_iri, *args, **kwargs)

        # Actually save this to the database
        super(BadgeObject, self).save()


class BadgeClass(BadgeObject):
    CLASS_TYPE = 'badgeclass'
    issuerorg = models.ForeignKey('badgeanalysis.IssuerOrg', blank=True, null=True)

    def save(self, *args, **kwargs):
        # If existing_badgeclass hasn't already been tested, do that.
        if kwargs.get(self.iri, None) != 'new':
            existing_badgeclass = BadgeClass.detect_existing(self.iri)
            if existing_badgeclass is not None:
                return existing_badgeclass

        try:
            super(BadgeClass, self).save(*args, **kwargs)
        except Exception as e:
            raise e
            return

        issuerorg_iri = self.badge_object.get('issuer')
        self.issuerorg = IssuerOrg.get_or_create_by_iri(issuerorg_iri, *args, **kwargs)

        # Actually save this to the database
        super(BadgeObject, self).save()


class IssuerOrg(BadgeObject):
    CLASS_TYPE = 'issuerorg'

    def save(self, *args, **kwargs):
        # If existing_issuerorg hasn't already been tested, do that.
        if kwargs.get(self.iri, None) != 'new':
            existing_issuerorg = IssuerOrg.detect_existing(self.iri)
            if existing_issuerorg is not None:
                return existing_issuerorg

        try:
            super(IssuerOrg, self).save(*args, **kwargs)
        except Exception as e:
            raise e
            return

        # Actually save this to the database
        super(BadgeObject, self).save()


# TO DO: implement extension
class Extension():
    CLASS_TYPE = 'extension'


# Grabs the appropriate class, so we can say things like:
# badge_object_class('assertion').processBadgeObject(badgeObject)
def badge_object_class(objectType):
    if objectType == 'assertion':
        return Assertion
    elif objectType == 'badgeclass':
        return BadgeClass
    elif objectType == 'issuerorg':
        return IssuerOrg
    elif objectType == 'extension':
        return Extension
    else:
        return BadgeObject
