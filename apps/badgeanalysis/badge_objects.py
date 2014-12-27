# utility methods for analyzing badge objects
# (Assertions, BadgeClasses, IssuerOrgs, and Extensions)
# in general, and for each specific case, allowing us to run the
# appropriate validations and manipulations for each case without
# embedding all that logic in the procedure itself.

import json
from validation_messages import BadgeValidationSuccess, BadgeValidationError
import badgeanalysis.utils
from scheme_models import BadgeScheme


class BadgeObject(object):
    CLASS_TYPE = 'unknown'

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
        badgeObject = badgeMetaObject.get('badgeObject')

        # If we have JSON as a string, try to load it before treating it as a potential URL
        if not isinstance(badgeObject, dict):
            badgeObject = badgeanalysis.utils.try_json_load(badgeObject)

        # In the likely event that we have a url string as our input badgeObject
        if isinstance(badgeObject, (str, unicode)) and badgeanalysis.utils.test_probable_url(badgeObject):
            badgeMetaObject['id'] = badgeObject
            try:
                badgeObject = json.loads(docloader(badgeObject))
            except Exception as e:
                raise TypeError(
                    "Couldn't fetch badgeObject on input. We tried to load "
                    + badgeObject + " -- got error " + e
                )
                return

        #CASE 1: For OBI version 1.1 and later, the badgeObject will have JSON-LD context information.
        if badgeanalysis.utils.has_context(badgeObject):
            context = badgeObject.get('@context')

            # Determine if the existing context has a suitable main OBI context within it.
            if isinstance(context, (str, list)):
                badgeMetaObject['context'] = badgeanalysis.utils.validateMainContext(context)

            # Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
            elif isinstance(context, dict):
                raise TypeError(
                    "OBI context not linked at top level of input object. This isn't a declared OBI object. Here's the context: "
                    + context
                )

            if '@type' in badgeObject:
                #TODO this is likely not going to be the full expanded IRI, likely a fragment
                badgeMetaObject['type'] = badgeanalysis.utils.validateObiType(badgeObject['@type'])
            else:
                #TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
                # For now, assume we can guess the type correctly
                badgeMetaObject['type'] = cls.CLASS_TYPE
                badgeMetaObject['badgeObject']['@type'] = cls.CLASS_TYPE

        # CASE 2: For OBI versions 0.5 and 1.0, we will have to deterimine how to add JSON-LD context information.
        else:
            #TODO: In progress, Use the BadgeScheme class to divine which of the old formats it might be.
            matchingScheme = BadgeScheme.get_legacy_scheme_match(badgeObject, cls.CLASS_TYPE)
            if matchingScheme is None:
                raise TypeError("Could not determine type of badge object with known schema set")
                return None

            else:
                # record results of schema matching process
                badgeMetaObject['context'] = matchingScheme['context_url']
                badgeMetaObject['type'] = matchingScheme['type']
                badgeMetaObject['scheme'] = matchingScheme['scheme']

        """ Finalize badge object by adding the @id if possible """
        if 'id' in badgeMetaObject and not '@id' in badgeObject:
            badgeMetaObject['badgeObject']['@id'] = badgeanalysis.utils.validateId(badgeMetaObject['id'])
        elif '@id' in badgeObject:
            badgeMetaObject['id'] = badgeanalysis.utils.validateId(badgeObject['@id'])
        elif 'verify' in badgeObject and 'type' in badgeObject['verify'] and badgeObject['verify']['type'] == 'hosted' and 'url' in badgeObject['verify']:
            potentialId = badgeanalysis.utils.validateId(badgeObject['verify']['url'])
            badgeMetaObject['badgeObject']['@id'] = potentialId
            badgeMetaObject['id'] = potentialId

        return badgeMetaObject


class Assertion(BadgeObject):
    CLASS_TYPE = 'assertion'

    @classmethod
    def processBadgeObject(cls, badgeMetaObject, docloader=badgeanalysis.utils.fetch_linked_component, **kwargs):
        """
        Might require kwargs['recipient_input'] if assertion.recipient.hashed == true.
        Return error if recipient_input is missing when required or doesn't match hash.
        """
        # perform base processing unless override flag is present
        if not kwargs.get('already_base_processed', False):
            badgeMetaObject = super(Assertion, cls).processBadgeObject(badgeMetaObject, docloader, **kwargs)

        # for assertion objects, we must always fetch the original and use that for validation,
        # rather than relying on what is supplied in a baked image or input JSON.
        try:
            real_assertion = docloader(badgeMetaObject.get('id'))
        except:
            badgeMetaObject['errors'] = badgeMetaObject.get('errors', [])
            badgeMetaObject['errors'].append(
                str(
                    BadgeValidationError(
                        "Could not fetch the original assertion of supplied badge: "
                        + badgeMetaObject.get('id', json.dumps(badgeMetaObject)),
                        "RecipientRequiredValidator"
                    )
                )
            )
            return badgeMetaObject
        else:
            # We're overwriting the original here. For some advanced future validation, we may want to diff the two.
            badgeMetaObject = super(Assertion, cls).processBadgeObject({'badgeObject': real_assertion}, **kwargs)

        # Deterimine if identifier is included (unhashed) or must be provided:
        # Case 1: identifier is missing
        if kwargs.get('recipient_input') is None:
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
                    str(
                        BadgeValidationError(
                            "Recipient ID is hashed and no recipient_input provided",
                            "RecipientRequiredValidator"
                        )
                    )
                )

            else:
                badgeMetaObject['notes'] = badgeMetaObject.get('notes', [])
                badgeMetaObject['notes'].append(
                    str(
                        BadgeValidationSuccess(
                            "Recipient input not needed, embedded recipient identity is not hashed",
                            "RecipientRequiredValidator"
                        )
                    )
                )

        # If recipient_input is provided, make sure it matches the hashed string.
        else:
            # TODO Add AssertionRecipientValidator to the list of validators to be run on this badge.
            pass

        return badgeMetaObject


class BadgeClass(BadgeObject):
    CLASS_TYPE = 'badgeclass'


class IssuerOrg(BadgeObject):
    CLASS_TYPE = 'issuerOrg'


class Extension(BadgeObject):
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
