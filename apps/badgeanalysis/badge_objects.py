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
        docloader = kwargs.get('docloader', badgeanalysis.utils.fetch_linked_component)

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
            new_object.save(*args, **kwargs)
            return new_object

    @classmethod
    def get_or_create_by_badge_object(cls, badge_input, *args, **kwargs):
        # If we have JSON as a string, try to load it before treating it as a potential URL
        if not isinstance(badge_input, dict):
            processed_input = badgeanalysis.utils.try_json_load(badge_input)

        # If we've got a URL, create this object from the URL.
        if isinstance(processed_input, (str, unicode)):
            if badgeanalysis.utils.test_probable_url(processed_input):
                return cls.get_or_create_by_iri(processed_input, *args, **kwargs)
            else:
                return BadgeValidationError("Did not know how to fetch badge object from " + processed_input, "unreadable URL", processed_input)

        # Else, figure out the hosted assertion URL, then create by that.
        if cls.CLASS_TYPE == 'assertion':
            badge_object_id = processed_input.get('@id', None) or processed_input.get('verify', {}).get('url', None)
            if badge_object_id is not None:
                return cls.get_or_create_by_iri(badge_object_id, *args, **kwargs)

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

        legacy_scheme = BadgeScheme.get_legacy_scheme_match(self.badge_object, self.CLASS_TYPE).get('scheme', None)
        if legacy_scheme is None:
            raise BadgeValidationError("Could not determine type of badge object with known schema set")

        return legacy_scheme

    def augment_badge_object_LD(self):
        """ Finalize badge object by adding the @id if possible """
        if '@id' not in self.badge_object:
            self.badge_object['@id'] = self.iri
        if '@type' not in self.badge_object:
            self.badge_object['@type'] = self.CLASS_TYPE
        if '@context' not in self.badge_object:
            self.badge_object['@context'] = self.scheme.context_url

    @classmethod
    def processBadgeObject(cls, badgeMetaObject, docloader=badgeanalysis.utils.fetch_linked_component, **kwargs):
        """
        Format of a badgeMetaObject -- if needed property doesn't exist on input,
        create it upon use.

        badgeMetaObject = {
            badgeObject: {dict},
            type: 'str',
            id: 'str',
            context: 'str',
            scheme: BadgeScheme,
            errors: [],
            notes: [],
            # structures: {
            #     'typeKey': '/json/pointer/0'
            #     'extension': '/json/pointer/extension'
            # }
        }

        TODO: add above structures as processing result.
        """

        # If we have JSON as a string, try to load it before treating it as a potential URL
        if not isinstance(badgeMetaObject['badgeObject'], dict):
            badgeMetaObject['badgeObject'] = badgeanalysis.utils.try_json_load(badgeMetaObject['badgeObject'])

        # In the likely event that we have a url string as our input badgeMetaObject['badgeObject']
        if isinstance(badgeMetaObject['badgeObject'], (str, unicode)) and badgeanalysis.utils.test_probable_url(badgeMetaObject['badgeObject']):
            badgeMetaObject['id'] = badgeMetaObject['badgeObject']
            try:
                badgeMetaObject['badgeObject'] = badgeanalysis.utils.try_json_load(docloader(badgeMetaObject['id']))
            except Exception as e:
                raise TypeError(
                    "Couldn't fetch badgeMetaObject['badgeObject'] on input. We tried to load "
                    + badgeMetaObject['badgeObject'] + " -- got error " + e.message
                )
                return

        #CASE 1: For OBI version 1.1 and later, the badgeMetaObject['badgeObject'] will have JSON-LD context information.
        if badgeanalysis.utils.has_context(badgeMetaObject['badgeObject']):
            context = badgeMetaObject['badgeObject'].get('@context')

            # Determine if the existing context has a suitable main OBI context within it.
            if isinstance(context, (str, list)):
                badgeMetaObject['context'] = badgeanalysis.utils.validateMainContext(context)
            # Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
            elif isinstance(context, dict):
                raise TypeError(
                    "OBI context not linked at top level of input object. This isn't a declared OBI object. Here's the context: "
                    + context
                )

            if '@type' in badgeMetaObject['badgeObject']:
                #TODO this is likely not going to be the full expanded IRI, likely a fragment
                badgeMetaObject['type'] = badgeanalysis.utils.validateObiType(badgeMetaObject['badgeObject']['@type'])
            else:
                #TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
                # For now, assume we can guess the type correctly
                badgeMetaObject['type'] = cls.CLASS_TYPE
                badgeMetaObject['badgeObject']['@type'] = cls.CLASS_TYPE

            badgeMetaObject['scheme'] = BadgeScheme.objects.get(slug='1_1')

        # CASE 2: For OBI versions 0.5 and 1.0, we will have to deterimine how to add JSON-LD context information.
        else:
            #TODO: In progress, Use the BadgeScheme class to divine which of the old formats it might be.

            matchingScheme = BadgeScheme.get_legacy_scheme_match(badgeMetaObject['badgeObject'], cls.CLASS_TYPE)
            if matchingScheme is None:
                raise TypeError("Could not determine type of badge object with known schema set")
                return None

            else:
                # record results of schema matching process
                badgeMetaObject['context'] = matchingScheme['context_url']
                badgeMetaObject['type'] = matchingScheme['type']
                badgeMetaObject['scheme'] = matchingScheme['scheme']

        """ Finalize badge object by adding the @id if possible """
        if 'id' in badgeMetaObject and not '@id' in badgeMetaObject['badgeObject']:
            badgeMetaObject['badgeObject']['@id'] = badgeanalysis.utils.validateId(badgeMetaObject['id'])
        elif '@id' in badgeMetaObject['badgeObject']:
            badgeMetaObject['id'] = badgeanalysis.utils.validateId(badgeMetaObject['badgeObject']['@id'])
        elif 'verify' in badgeMetaObject['badgeObject'] and 'type' in badgeMetaObject['badgeObject']['verify'] and badgeMetaObject['badgeObject']['verify']['type'] == 'hosted' and 'url' in badgeMetaObject['badgeObject']['verify']:
            potentialId = badgeanalysis.utils.validateId(badgeMetaObject['badgeObject']['verify']['url'])
            badgeMetaObject['badgeObject']['@id'] = potentialId
            badgeMetaObject['id'] = potentialId

        return badgeMetaObject


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
        super(Assertion, self).save(*args, **kwargs)

        badgeclass_iri = self.badge_object.get('badge')
        self.badgeclass = BadgeClass.get_or_create_by_iri(badgeclass_iri, *args, **kwargs)

        # Actually save this to the database
        super(BadgeObject, self).save()

    @classmethod
    def processBadgeObject(cls, badgeMetaObject, docloader=badgeanalysis.utils.fetch_linked_component, **kwargs):
        """
        Might require kwargs['recipient_input'] if assertion.recipient.hashed == true.
        Return error if recipient_input is missing when required or doesn't match hash.
        """
        recipient_input = badgeMetaObject.get('recipient_input')
        # perform base processing unless override flag is present
        if not kwargs.get('already_base_processed', False):
            badgeMetaObject = super(Assertion, cls).processBadgeObject(badgeMetaObject, docloader, **kwargs)

        # for assertion objects, we must always fetch the original and use that for validation,
        # rather than relying on what is supplied in a baked image or input JSON.
        try:
            # TODO, make sure id is included in all possible badgeMetaObjects
            real_assertion = docloader(badgeMetaObject.get('id'))
        except:
            badgeMetaObject['errors'] = badgeMetaObject.get('errors', [])
            badgeMetaObject['errors'].append(
                BadgeValidationError(
                    "Could not fetch the original assertion of supplied badge: "
                    + badgeMetaObject.get('id', json.dumps(badgeMetaObject)),
                    "RecipientRequiredValidator"
                )
            )
            return badgeMetaObject
        else:
            # We're overwriting the original here. For some advanced future validation, we may want to diff the two.
            badgeMetaObject['badgeObject'] = real_assertion
            badgeMetaObject = super(Assertion, cls).processBadgeObject(badgeMetaObject, **kwargs)

        # Deterimine if identifier is included (unhashed) or must be provided:
        # Case 1: identifier is missing
        if recipient_input is None:
            # determine if we have an ambiguous hashed identifier
            def id_needed():
                try:
                    is_hashed = badgeMetaObject['badgeObject']['recipient']['hashed']
                except Exception:
                    # If we can't find it in the 1.x spot, try the 0.5 spot
                    try:
                        is_hashed = badgeMetaObject['badgeObject']['salt']
                    except Exception:
                        # if there's no salt, it's not a hashed 0.5 badge, hence plaintext
                        return False
                    else:
                        return True
                else:
                    return is_hashed

            if id_needed():
                # record error in log
                badgeMetaObject['errors'] = badgeMetaObject.get('errors', [])
                badgeMetaObject['errors'].append(
                    BadgeValidationError(
                        "Recipient ID is hashed and no recipient_input provided",
                        "RecipientRequiredValidator"
                    )
                )

            else:
                badgeMetaObject['notes'] = badgeMetaObject.get('notes', [])
                badgeMetaObject['notes'].append(
                    BadgeValidationSuccess(
                        "Recipient input not needed, embedded recipient identity is not hashed",
                        "RecipientRequiredValidator"
                    )
                )

        # If recipient_input is provided, make sure it matches the hashed string.
        else:
            # if not badgeMetaObject.get('recipient_input'):
            recipient_hash_validation = assertionRecipientValidator.validate(assertionRecipientValidator, badgeMetaObject)
            if isinstance(recipient_hash_validation, BadgeValidationSuccess):
                badgeMetaObject['notes'] = badgeMetaObject.get('notes', [])
                badgeMetaObject['notes'].append(recipient_hash_validation.to_dict())
            else:
                badgeMetaObject['errors'] = badgeMetaObject.get('errors', [])
                badgeMetaObject['errors'].append(recipient_hash_validation.to_dict())

        return badgeMetaObject


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
