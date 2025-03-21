# encoding: utf-8
import io
import json
import os
import urllib.parse
from json import dumps as json_dumps

import dateutil.parser
from django.core.files.base import ContentFile
from django.core.files.storage import DefaultStorage
from django.db import models, transaction
from django.urls import resolve, Resolver404
from openbadges_bakery import bake

from issuer.utils import UNVERSIONED_BAKED_VERSION
from mainsite.utils import fetch_remote_file_to_storage, list_of, OriginSetting


def resolve_source_url_referencing_local_object(source_url):
    if source_url.startswith(OriginSetting.HTTP):
        try:
            match = resolve(urllib.parse.urlparse(source_url).path)
            return match
        except Resolver404:
            pass


class BaseOpenBadgeObjectManager(models.Manager):
    def get_local_object(self, source_url):
        match = resolve_source_url_referencing_local_object(source_url)
        if match:
            try:
                return self.get(entity_id=match.kwargs.get('entity_id'))
            except self.model.DoesNotExist:
                return None


class IssuerManager(BaseOpenBadgeObjectManager):
    @transaction.atomic
    def get_or_create_from_ob2(self, issuer_obo, source=None, original_json=None):
        source_url = issuer_obo.get('id')
        local_object = self.get_local_object(source_url)
        if local_object:
            return local_object, False

        image_url = issuer_obo.get('image', None)
        image = None
        if image_url:
            if isinstance(image_url, dict):
                image_url = image_url.get('id')
            image = _fetch_image_and_get_file(image_url, upload_to='remote/issuer')
        return self.get_or_create(
            source_url=source_url,
            defaults=dict(
                source=source if source is not None else 'local',
                name=issuer_obo.get('name'),
                description=issuer_obo.get('description', None),
                url=issuer_obo.get('url', None),
                email=issuer_obo.get('email', None),
                image=image,
                original_json=original_json,
            ),
        )


class BadgeClassManager(BaseOpenBadgeObjectManager):
    @transaction.atomic
    def create(self, **kwargs):
        new_kwargs = {key: value for (key, value) in kwargs.items() if key != 'award_allowed_institutions'}
        obj = self.model(**new_kwargs)
        obj.award_allowed_institutions.set(kwargs.get('award_allowed_institutions', []))
        obj.save()
        return obj

    @transaction.atomic
    def get_or_create_from_ob2(self, issuer, badgeclass_obo, source=None, original_json=None):
        source_url = badgeclass_obo.get('id')
        local_object = self.get_local_object(source_url)
        if local_object:
            return local_object, False

        criteria_text = None
        criteria = badgeclass_obo.get('criteria', None)
        if isinstance(criteria, str):
            criteria_text = criteria
        elif criteria.get('type', 'Criteria') == 'Criteria':
            criteria_text = criteria.get('narrative', None)

        image_url = badgeclass_obo.get('image')
        if isinstance(image_url, dict):
            image_url = image_url.get('id')
        image = _fetch_image_and_get_file(image_url, upload_to='remote/badgeclass')

        return self.get_or_create(
            source_url=source_url,
            defaults=dict(
                issuer=issuer,
                source=source if source is not None else 'local',
                name=badgeclass_obo.get('name'),
                description=badgeclass_obo.get('description', None),
                image=image,
                criteria_text=criteria_text,
                original_json=original_json,
            ),
        )


def _fetch_image_and_get_file(url, upload_to=''):
    status_code, storage_name = fetch_remote_file_to_storage(url, upload_to=upload_to)
    if status_code == 200:
        image = DefaultStorage().open(storage_name)
        image.name = storage_name
        return image


class BadgeInstanceManager(BaseOpenBadgeObjectManager):
    @transaction.atomic
    def get_or_create_from_ob2(self, badgeclass, assertion_obo, recipient_identifier, source=None, original_json=None):
        source_url = assertion_obo.get('id')
        local_object = self.get_local_object(source_url)
        if local_object:
            return local_object, False

        image_url = assertion_obo.get('image', None)
        image = None
        if image_url is None:
            image = badgeclass.image.file
        else:
            if isinstance(image_url, dict):
                image_url = image_url.get('id')
            image = _fetch_image_and_get_file(image_url, upload_to='remote/assertion')

        issued_on = None
        if 'issuedOn' in assertion_obo:
            issued_on = dateutil.parser.parse(assertion_obo.get('issuedOn'))

        badgeinstance, created = self.get_or_create(
            source_url=assertion_obo.get('id'),
            defaults=dict(
                recipient_identifier=recipient_identifier,
                hashed=assertion_obo.get('recipient', {}).get('hashed', True),
                source=source if source is not None else 'local',
                original_json=original_json,
                badgeclass=badgeclass,
                issuer=badgeclass.cached_issuer,
                image=image,
                acceptance=self.model.ACCEPTANCE_ACCEPTED,
                narrative=assertion_obo.get('narrative', None),
                issued_on=issued_on,
            ),
        )
        if created:
            evidence = list_of(assertion_obo.get('evidence', None))
            if evidence:
                from issuer.models import BadgeInstanceEvidence

                for evidence_item in evidence:
                    BadgeInstanceEvidence.objects.create_from_ob2(badgeinstance, evidence_item)

        return badgeinstance, created

    def create(self, evidence=None, extensions=None, allow_uppercase=False, **kwargs):
        """
        Convenience method to award a badge to a recipient_id
        :param allow_uppercase: bool
        :type badgeclass: BadgeClass
        :type issuer: Issuer
        """
        recipient_identifier = kwargs.pop('recipient_identifier')
        recipient_identifier = recipient_identifier if allow_uppercase else recipient_identifier.lower()

        badgeclass = kwargs.pop('badgeclass', None)
        issuer = kwargs.pop('issuer', badgeclass.issuer)

        # self.model would be a BadgeInstance
        new_instance = self.model(
            public=False, recipient_identifier=recipient_identifier, badgeclass=badgeclass, issuer=issuer, **kwargs
        )

        with transaction.atomic():
            new_instance.save()

            badgeclass_name, ext = os.path.splitext(new_instance.badgeclass.image.file.name)
            new_image = io.BytesIO()
            bake(
                image_file=new_instance.cached_badgeclass.image.file,
                assertion_json_string=json_dumps(
                    new_instance.get_json(obi_version=UNVERSIONED_BAKED_VERSION), indent=2
                ),
                output_file=new_image,
            )
            new_instance.image.save(
                name='assertion-{id}{ext}'.format(id=new_instance.entity_id, ext=ext),
                content=ContentFile(new_image.read()),
                save=False,
            )
            new_instance.save()

            if evidence is not None:
                from issuer.models import BadgeInstanceEvidence

                for evidence_obj in evidence:
                    BadgeInstanceEvidence.objects.create(
                        badgeinstance=new_instance,
                        evidence_url=evidence_obj.get('evidence_url'),
                        narrative=evidence_obj.get('narrative'),
                        name=evidence_obj.get('name'),
                        description=evidence_obj.get('description'),
                    )
            if extensions is not None:
                for name, ext in list(extensions.items()):
                    new_instance.badgeinstanceextension_set.create(name=name, original_json=json.dumps(ext))

        return new_instance


class BadgeInstanceEvidenceManager(models.Manager):
    @transaction.atomic
    def create_from_ob2(self, badgeinstance, evidence_obo):
        return self.create(
            badgeinstance=badgeinstance,
            evidence_url=evidence_obo.get('id', None),
            narrative=evidence_obo.get('narrative', None),
            name=evidence_obo.get('name', None),
            description=evidence_obo.get('description', None),
            original_json=json.dumps(evidence_obo),
        )
