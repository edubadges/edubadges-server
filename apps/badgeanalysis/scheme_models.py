from django.db import models
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned

from pyld import jsonld

from jsonschema import validate, Draft4Validator, draft4_format_checker
from jsonschema.exceptions import ValidationError  # , FormatError

import basic_models

from jsonfield import JSONField

import badgeanalysis.utils
from functional_validators import BadgeFunctionalValidator, FunctionalValidatorList
from validation_messages import BadgeValidationSuccess, BadgeValidationError, BadgeValidationMessage


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
        contextObj = badgeanalysis.utils.try_json_load(self.context_json)
        validators = contextObj.get('obi:validation')
        if validators is not None and isinstance(validators, list):
            for validator in validators:
                validationSchema = validator.get('obi:validationSchema')
                validatesType = validator.get('obi:validatesType')
                schema_json = badgeanalysis.utils.try_json_load(badgeanalysis.utils.fetch_linked_component(validationSchema))

                bsv = BadgeSchemaValidator(validation_schema=validationSchema, validates_type=validatesType, schema_json=schema_json, scheme=self)

                bsv.save()
        elif isinstance(validators, dict):
            bsv = BadgeSchemaValidator(self, validation_schema=validators.get('obi:validationSchema'), validates_type=validators.get('obi:validatesType'), scheme=self)
            bsv.save()

    def save(self, *args, **kwargs):
        if not self.pk:
            if self.context_json is None:
                # TODO: add validation step
                self.context_json = badgeanalysis.utils.try_json_load(badgeanalysis.utils.fetch_linked_component(self.context_url))

            elif isinstance(self.context_json, (str, unicode)):
                self.context_json = badgeanalysis.utils.try_json_load(self.context_json)

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
    def get_legacy_scheme_match(cls, badgeObject, badgeObjectType, known_slug=None):
        LEGACY_SLUGS = ['0_5', '1_0-backpack-misbaked', '1_0']

        search_slug = [known_slug] if known_slug is not None else LEGACY_SLUGS
        if badgeObjectType == 'issuer':
            badgeObjectType = 'issuerorg'
        VALID_TYPES = ['assertion', 'badgeclass', 'issuerorg']

        if not badgeObjectType in VALID_TYPES:
            raise TypeError("Input type " + badgeObjectType + " isn't one of the valid options: " + str(VALID_TYPES))

        schemes = cls.objects.filter(slug__in=LEGACY_SLUGS).prefetch_related('schemes')

        # Here's the first schema_json:
        # schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].schema_json

        # heres the type one validates:
        # schemes[0]._prefetched_objects_cache['schemes']._result_cache[0].validates_type

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
        def insert_into_tree(scheme, schemaSlug, contextUrl, schemaJson, tree=schemaTree[badgeObjectType]):
            if 'test' in tree and tree['test'] == schemaSlug:
                tree['context_url'] = contextUrl
                tree['schema_json'] = schemaJson
                tree['scheme'] = scheme
                return tree
            elif 'noMatch' in tree:
                return insert_into_tree(scheme, schemaSlug, contextUrl, schemaJson, tree['noMatch'])
            return None

        for scheme in schemes:
            currentSchemaJson = None
            for validator in scheme._prefetched_objects_cache['schemes']._result_cache:
                if validator.validates_type == badgeObjectType:
                    currentSchemaJson = validator.schema_json

                if insert_into_tree(scheme, scheme.slug, scheme.context_url, currentSchemaJson) is None:
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
                "schemeSlug": treeMatch['test'],
                "scheme": treeMatch['scheme']
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
    def test_against_schema_verbose(cls, badgeObject, schemaJson):
        """
        Reads the specified schema based on the filename registered for schemaKey, and processes it into an object with json.loads()
        Then validates the badge object against it.
        """
        try:
            validate(badgeObject, schemaJson, Draft4Validator, format_checker=draft4_format_checker)
        except ValidationError as e:
            return str(e)
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