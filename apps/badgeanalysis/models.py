from django.db import models
from django.conf import settings
from urlparse import urljoin
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core.urlresolvers import reverse

import re
from pyld import jsonld
import json

from jsonschema import validate, Draft4Validator, draft4_format_checker
from jsonschema.exceptions import ValidationError  # , FormatError

import basic_models
from djangosphinx.models import SphinxSearch
from jsonfield import JSONField

import badgeanalysis.utils



class BadgeScheme(basic_models.SlugModel):
    default_type = models.CharField(max_length=64)
    context_url = models.URLField(verbose_name='URL location of the JSON-LD context file core to this scheme', max_length=2048)
    description = models.TextField(blank=True)
    context_json = JSONField(blank=True)

    def get_form(self):
        from badges.forms import BadgeSchemeForm
        return BadgeSchemeForm(instance=self)

    def registerValidators(self):
        # TODO: Use JSON-LD for this?
        contextObj = json.loads(self.context_json)
        validators = contextObj.get('obi:validation')
        if validators is not None and isinstance(validators, list):
            for validator in validators:
                validationSchema = validator.get('obi:validationSchema')
                validatesType = validator.get('obi:validatesType')
                schema_json = json.loads(badgeanalysis.utils.fetch_linked_component(validationSchema))

                bsv = BadgeSchemaValidator(validation_schema=validationSchema, validates_type=validatesType, schema_json=schema_json, scheme=self)

                bsv.save()
        elif isinstance(validators, dict):
            bsv = BadgeSchemaValidator(self, validation_schema=validators.get('obi:validationSchema'), validates_type=validators.get('obi:validatesType'), scheme=self)
            bsv.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.context_json is None:
                self.context_json = badgeanalysis.utils.fetch_linked_component(self.context_url)

            super(BadgeScheme, self).save(*args, **kwargs)

            self.registerValidators()

        else:
            super(BadgeScheme, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('badgescheme_detail', args=[self.slug])

    @classmethod
    def get_context_file_by_url(cls, url):
        try:
            result = cls.objects.get(context_url=url)
        except MultipleObjectsReturned as e:
            raise e
        except ObjectDoesNotExist:
            return None
        else:
            return result.context_json

    @classmethod
    def get_legacy_scheme_match(cls, badgeObject, badgeObjectType):
        LEGACY_SLUGS = ['0_5', '1_0-backpack-misbaked', '1_0']
        if badgeObjectType == 'issuer':
            badgeObjectType = 'issuerorg'
        VALID_TYPES = ['assertion', 'badgeclass', 'issuerorg']

        if not badgeObjectType in VALID_TYPES:
            raise TypeError("Input type " + badgeObjectType + " isn't one of the valid options: " + VALID_TYPES)

        schemes = cls.objects.filter(slug__in=LEGACY_SLUGS).prefetch_related('schemes')

        # Here's the first schema_json:
        schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].schema_json

        # heres the type one validates:
        schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].validates_type

        # build a dict of schema_json that match our type
        schemaTree = {}
        schemaTree['assertion'] = {
            'test': '0_5',  # 'http://localhost:8000/static/0.5/schema/assertion',
            'noMatch': {
                'test': '1_0-backpack-misbaked',  # 'http://localhost:8000/static/0.5/schema/backpack_error_assertion',
                'noMatch': { 
                    'test': '1_0',  # 'http://localhost:8000/static/1.0/schema/assertion'
                }
            }
        }
        schemaTree['badgeclass'] = {
            'test': '1_0'
        }
        schemaTree['issuerorg'] = {
            'test': '1_0'
        }

        # A function to put the JSON of the schema into the tree structure so it can be easily accessed.
        def insert_into_tree(schemaSlug, contextUrl, schemaJson, tree=schemaTree[badgeObjectType]):
            if 'test' in tree and tree['test'] == schemaSlug:
                tree['context_url'] = contextUrl
                tree['schema_json'] = schemaJson
                return tree
            elif 'noMatch' in tree:
                return insert_into_tree(schemaSlug, contextUrl, schemaJson, tree['noMatch'])
            return None

        for scheme in schemes:
            currentSchemaJson = None
            for validator in scheme._prefetched_objects_cache['schemes']._result_cache:
                if validator.validates_type == badgeObjectType:
                    currentSchemaJson = validator.schema_json

                if insert_into_tree(scheme.slug, scheme.context_url, currentSchemaJson) is None:
                    # raise LookupError("Could not insert schema json for " + scheme.slug + " into tree")
                    pass

        try:
            treeMatch = cls.test_against_schema_tree(badgeObject, schemaTree[badgeObjectType])
        except LookupError as e:
            raise e

        if treeMatch:
            return {
                "context_url": treeMatch['context_url'],
                "type": badgeObjectType,
                "schemeSlug": treeMatch['test']
            }
        else:
            return None

    @classmethod
    def test_against_schema_tree(cls, badgeObject, testTree):
        if not 'test' in testTree:
            raise LookupError("Schema Tree malformed, could not find a test reference when needed. " + str(testTree))
            return None

        if cls.test_against_schema(badgeObject, testTree['schema_json']):
            # There are only more tests down the noMatch path, so we can return right here.
            return testTree
        elif 'noMatch' in testTree:
            return cls.test_against_schema_tree(badgeObject, testTree['noMatch'])
        else:
            return None

    @classmethod
    def test_against_schema(cls, badgeObject, schemaJson):
        """
        Reads the specified schema based on the filename registered for schemaKey, and processes it into an object with json.loads()
        Then validates the badge object against it.
        """
        try:
            validate(badgeObject, schemaJson, Draft4Validator, format_checker=draft4_format_checker)
        except ValidationError:
            return False
        else:
            return True

    @classmethod
    def custom_context_docloader(cls, url):
        # TODO: This is called from OpenBadge.init_badge_analysis, and might be called multiple times,
        # with a DB hit for each.
        context_json = cls.get_context_file_by_url(url)
        if context_json is not None:
            doc = {
                'contextUrl': None,
                'documentUrl': url,
                'document': context_json
            }
            return doc

        #fall back to default document loader
        return jsonld.load_document(url)


class BadgeSchemaValidator(basic_models.DefaultModel):
    scheme = models.ForeignKey(BadgeScheme, related_name='schemes')
    validates_type = models.CharField(max_length=2048)
    validation_schema = models.URLField(verbose_name='URL location of the validation schema', max_length=2048)
    schema_json = JSONField(blank=True)

    def save(self, *args, **kwargs):
        if not self.pk:

            try:
                result = BadgeSchemaValidator.objects.get(validation_schema=self.validation_schema)
            except MultipleObjectsReturned:
                pass
            except ObjectDoesNotExist:
                try:
                    Draft4Validator.check_schema(self.schema_json)
                except Exception as e:
                    raise e
                else:
                    super(BadgeSchemaValidator, self).save(*args, **kwargs)

        # Save the model if it's an update.
        else:
            super(BadgeSchemaValidator, self).save(*args, **kwargs)


class OpenBadge(basic_models.DefaultModel):
    """
    Each OpenBadge contains an input Badge Object and corresponding metadata built up as a result of analysis.

    self.badge_input: string -- The badgeObject input to the library to analyze
    self.full_badge_object: (JSONField) dict of dicts -- of badgeObjects composed to add up to this badgeObject
    self.verify_method: string -- 'hosted' or 'signed'
    self.errors: list -- a list of critical OpenBadgeErrors
    self.notes: list -- a list of validation passes and noncritical failures
    """
    image = models.ImageField(upload_to=badgeanalysis.utils.image_upload_to(), blank=True)
    badge_input = models.TextField(blank=True, null=True)
    recipient_input = models.CharField(blank=True, max_length=2048)
    full_badge_object = JSONField()
    full_ld_expanded = JSONField()
    verify_method = models.CharField(max_length=48, blank=True)
    errors = JSONField()
    notes = JSONField()

    scheme = models.ForeignKey(BadgeScheme, blank=True, null=True)

    search = SphinxSearch()

    def __unicode__(self):
        badge_name = self.getProp('badgeclass', 'name')
        badge_issuer = self.getProp('issuerorg', 'name')

        return "Open Badge: " + badge_name + ", issued by " + badge_issuer + " to " + self.recipient_input

    # Core procedure for filling out an OpenBadge from an initial badgeObject follows:
    def save(self, *args, **kwargs):
        if not self.pk:
            self.init_badge_analysis(*args, **kwargs)

        # finally, save the OpenBadge after doing all that stuff in case it's a new one
        super(OpenBadge, self).save(*args, **kwargs)

    def init_badge_analysis(self, *args, **kwargs):
        """
        Stores the input object and sets up a fullBadgeObject to fill out
        and analyze
        """
        if not self.image and self.recipient_input:
            raise IOError("Invalid input to OpenBadge create: " + kwargs['image'])

        self.errors = []
        self.notes = []

        try:
            self.badge_input = badgeanalysis.utils.extract_assertion_from_image(self.image)
        except Exception as e:
            self.errors.append(e)
            raise e
            return

        self.verify_method = 'hosted'  # signed not yet supported.

        # Process the initial input
        # Returns a dict with badgeObject property for processed object and 'type', 'context', 'id' properties
        try:
            structureMeta = self.processBadgeObject(self.badge_input,'assertion')
        except TypeError as e:
            self.errors.append(e)
            raise e
            return

        if not structureMeta['badgeObject']:
            raise IOError("Could not build a full badge object without having a properly stored inputObject")

        full = {
            '@context': structureMeta['context'] or 'http://standard.openbadges.org/1.1/context',
            '@type': 'obi:OpenBadge'
        }
        # place the validated input object into 
        full[structureMeta['type']] = structureMeta['badgeObject'].copy()

        """
        # Build out the full badge object by fetching missing components.

        #TODO: refactor. This is kind of clunky. Maybe some recursion would help
        #TODO: refactor to consider the future possibility of issuer defined in the assertion 
        #(or separate issuers defined in assertion & issuer, both cases requiring authorization)
        """
        try:
            if isinstance(full['assertion'], dict) and not 'badgeclass' in full:
                # For 1.0 etc compliant badges with linked badgeclass
                if isinstance(full['assertion']['badge'], (str, unicode)):
                    theBadgeClass = badgeanalysis.utils.fetch_linked_component(full['assertion']['badge'])
                    theBadgeClass = self.processBadgeObject(theBadgeClass, 'badgeclass')
                    if theBadgeClass['type'] == 'badgeclass':
                        full['badgeclass'] = theBadgeClass['badgeObject']
                # for nested badges (0.5 & backpack-wonky!) (IS THIS REALLY A GOOD IDEA??
                # It won't have a schema to match up against.)
                # For backpack-wonky, we should instead build our badge object based on the originally issued assertion,
                # not the baked one.
                elif isinstance(full['assertion']['badge'], dict):
                    full['badgeclass'] = full['assertion']['badge']

            if isinstance(full['badgeclass'], dict) and not 'issuerorg' in full:
                if isinstance(full['badgeclass']['issuer'], (str, unicode)):
                    theIssuerOrg = badgeanalysis.utils.fetch_linked_component(full['badgeclass']['issuer'])
                    theIssuerOrg = self.processBadgeObject(theIssuerOrg, 'issuerorg')
                    if theIssuerOrg['type'] == 'issuerorg':
                        full['issuerorg'] = theIssuerOrg['badgeObject']
                # Again, this is probably a bad idea like this?:
                elif isinstance(full['badgeclass']['issuer'], dict):
                    full['issuerorg'] = full['badgeclass']['issuer']
        except TypeError as e:
            #TODO: refactor to call a function to process the error. Raise it again for now.
            #self.errors.append({ "typeError": str(e)})
            raise e

        # Store results
        self.full_badge_object = full
        self.truncate_images()

        expand_options = {"documentLoader": BadgeScheme.custom_context_docloader}
        self.full_ld_expanded = jsonld.expand(full, expand_options)

    def processBadgeObject(self, badgeObject, probableType='assertion'):
        structureMeta = {}

        if not isinstance(badgeObject, dict):
            badgeObject = badgeanalysis.utils.try_json_load(badgeObject)

        if isinstance(badgeObject, (str, unicode)) and badgeanalysis.utils.test_probable_url(badgeObject):
            structureMeta['id'] = badgeObject
            try:
                badgeObject = badgeanalysis.utils.test_probable_url(badgeObject)
            except Exception as e:
                raise TypeError("Couldn't fetch badgeObject on input. We tried to load " + badgeObject + " -- got error " + e)
                return

        structureMeta['badgeObject'] = badgeObject

        """ CASE 1: For OBI version 1.1 and later, the badgeObject will have JSON-LD context information. """
        if badgeanalysis.utils.has_context(badgeObject):
            context = badgeObject.get('@context')

            # Determine if the existing context has a suitable main OBI context within it.
            if isinstance(context, (str, list)):
                structureMeta['context'] = self.validateMainContext(context)

            # Raise error if OBI context is not linked in the badge. Might still be a valid JSON-LD document otherwise
            elif isinstance(context, dict):
                raise TypeError("OBI context not linked at top level of input object. This isn't a declared OBI object. Here's the context: " + context)

            if '@type' in badgeObject:
                #TODO this is likely not going to be the full expanded IRI, likely a fragment
                structureMeta['type'] = self.validateObiType(badgeObject['@type'])
            else:
                #TODO schema-based matching for badge Classes that declared context but not type? Seems rare.
                # For now, assume we can guess the type correctly
                structureMeta['type'] = probableType
                structureMeta['badgeObject']['@type'] = probableType

            # """ CASE 2: For OBI versions 0.5 and 1.0, we will have to deterimine how to add JSON-LD context information. """
        else:

            #TODO: In progress, Use the BadgeScheme class to divine which of the old formats it might be.
            matchingScheme = BadgeScheme.get_legacy_scheme_match(badgeObject, probableType)
            if matchingScheme is None:
                raise TypeError("Could not determine type of badge object with known schema set")
                return None

            else:
                potentialContext = matchingScheme['context_url']
                structureMeta['context'] = potentialContext
                structureMeta['badgeObject']['@context'] = potentialContext

                potentialType = matchingScheme['type']
                structureMeta['type'] = potentialType
                structureMeta['badgeObject']['@type'] = potentialType

        """ Finalize badge object by adding the @id if possible """
        if 'id' in structureMeta and not '@id' in badgeObject:
            structureMeta['badgeObject']['@id'] = self.validateId(structureMeta['id'])
        elif '@id' in badgeObject:
            structureMeta['id'] = self.validateId(badgeObject['@id'])
        elif 'verify' in badgeObject and 'type' in badgeObject['verify'] and badgeObject['verify']['type'] == 'hosted' and 'url' in badgeObject['verify']:
            potentialId = self.validateId(badgeObject['verify']['url'])
            structureMeta['badgeObject']['@id'] = potentialId
            structureMeta['id'] = potentialId

        return structureMeta

    def truncate_images(self):
        dataUri = re.compile(r'^data:')

        full = self.full_badge_object
        if 'assertion' in full and 'image' in full['assertion']:
            if dataUri.match(full['assertion']['image']):
                del full['assertion']['image']  # remove dataUri from assertion. It would be totally weird to have one here anyway.
        if 'badgeclass' in full and 'image' in full['badgeclass']:
            if dataUri.match(full['badgeclass']['image']):
                full['badgeclass']['image'] = self.eventualImageUrl()

    def eventualImageUrl(self):
        # A dirty workaround for a 7-year old Django bug that filefields can't access the upload_to
        # parameter before they are saved.
        return urljoin(getattr(settings, 'MEDIA_URL'), badgeanalysis.utils.image_upload_to() + '/' + self.image.name)

    # TODO: This approach will not be able to handle issuers who redirect to an OBI context.
    def validateMainContext(self, contextInput):
        url = re.compile(r"standard\.openbadges\.org/[\d\.]+/context$")
        if isinstance(contextInput, str) and url.search(contextInput):
            return contextInput
        elif isinstance(contextInput, list):
            for contextElement in contextInput:
                if self.validateMainContext(contextElement):
                    return contextElement
        elif isinstance(contextInput, dict):
            # no need to accept these for now
            pass
        return None

    # Gets a simple string (compact IRI in the OBI context of the OBI object type)
    def validateObiType(self, typeInput):
        #TODO rework this with JSON-LD compaction instead of a simple in set operation. Gotta handle full IRIs

        if isinstance(typeInput, str) and typeInput in ('assertion', 'badgeclass', 'issuerorg'):
            return typeInput

        elif isinstance(typeInput, list):
            for typeElement in typeInput:
                elType = self.validateObiType(typeElement)
                if elType is not None:
                    return elType
        return None

    def validateId(self, idString):
        if badgeanalysis.utils.test_probable_url(idString):
            return idString
        return None

    # Tools to inspect an initialized badge object

    # Dangerous: We should use LD-based methods when possible to reduce cross-version problems.
    def getProp(self, parent, prop):
        sourceObject = self.full_badge_object.get(parent)
        return sourceObject.get(prop)

    # A wrapper for getLdProp that allows you to ask for the short version of a term in the 1.1 context.
    def ldProp(self, shortParent, shortProp):
        # normalize parent aliases to proper badge object IRI
        if shortParent in ("bc", "badgeclass"):
            parent = "http://standard.openbadges.org/definitions#BadgeClass"
        elif shortParent in ("asn", "assertion"):
            parent = "http://standard.openbadges.org/definitions#Assertion"
        elif shortParent in ("iss", "issuer", "issuerorg"):
            parent = "http://standard.openbadges.org/definitions#Issuer"

        iri = badgeanalysis.utils.get_iri_for_prop_in_current_context(shortProp)
        # import pdb; pdb.set_trace();

        return self.getLdProp(parent, iri)

    # TODO maybe: wrap this method to allow LD querying using the latest context's shorthand.
    # (so as to get the property we currently understand no matter what version the input object was)
    def getLdProp(self, parent, iri):
        if not parent in ('http://standard.openbadges.org/definitions#Assertion',
                          'http://standard.openbadges.org/definitions#BadgeClass',
                          'http://standard.openbadges.org/definitions#Issuer'):
            raise TypeError(parent + " isn't a known type of core badge object to search in")

        if not isinstance(self.full_ld_expanded, list) or not parent in self.full_ld_expanded[0]:
            return None
        parent_object = self.full_ld_expanded[0].get(parent)

        if not iri in parent_object[0]:
            return None
        temp = parent_object[0].get(iri)

        # TODO: With 1 property value for this IRI, either return the @value o
        # If there is more than one property value for this IRI, just return all
        if len(temp) == 1:
            if '@value' in temp[0]:
                return temp[0]['@value']
            elif isinstance(temp[0], dict) and '@id' in temp[0] and len(temp[0].keys()) < 2:
                return temp[0]['@id']
        return temp
