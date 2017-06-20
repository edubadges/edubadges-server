# encoding: utf-8
from __future__ import unicode_literals

import json

from django.core.files.storage import DefaultStorage
from django.db import models, transaction

from mainsite.utils import fetch_remote_file_to_storage
from pathway.tasks import award_badges_for_pathway_completion


class IssuerManager(models.Manager):

    @transaction.atomic
    def get_or_create_from_ob2(self, issuer_obo, source=None, original_json=None):
        image_url = issuer_obo.get('image', None)
        image = None
        if image_url:
           image = _fetch_image_and_get_file(image_url, upload_to='remote/issuer')
        return self.get_or_create(
            source_url=issuer_obo.get('id'),
            defaults=dict(
                source=source if source is not None else 'local',
                name=issuer_obo.get('name'),
                description=issuer_obo.get('description', None),
                url=issuer_obo.get('url', None),
                email=issuer_obo.get('email', None),
                image=image,
                original_json=original_json
            )
        )


class BadgeClassManager(models.Manager):

    @transaction.atomic
    def get_or_create_from_ob2(self, issuer, badgeclass_obo, source=None, original_json=None):
        criteria_url = None
        criteria_text = None
        criteria = badgeclass_obo.get('criteria', None)
        if isinstance(criteria, basestring):
            criteria_text = criteria
        elif criteria.get('type', 'Criteria') == 'Criteria':
            criteria_url = criteria.get('id', None)
            criteria_text = criteria.get('narrative', None)

        image = _fetch_image_and_get_file(badgeclass_obo.get('image'), upload_to='remote/badgeclass')

        return self.get_or_create(
            source_url=badgeclass_obo.get('id'),
            defaults=dict(
                issuer=issuer,
                source=source if source is not None else 'local',
                name=badgeclass_obo.get('name'),
                description=badgeclass_obo.get('description', None),
                image=image,
                criteria_url=criteria_url,
                criteria_text=criteria_text,
                original_json=original_json
            )
        )


class BadgeInstanceEvidenceManager(models.Manager):
    @transaction.atomic
    def create_from_ob2(self, badgeinstance, evidence_obo):
        return self.create(
            badgeintance=badgeinstance,
            evidence_url=evidence_obo.get('id', None),
            narrative=evidence_obo.get('narrative', None),
            original_json=json.dumps(evidence_obo)
        )


def _fetch_image_and_get_file(url, upload_to=''):
    status_code, storage_name = fetch_remote_file_to_storage(url, upload_to=upload_to)
    if status_code == 200:
        return DefaultStorage().open(storage_name)


class BadgeInstanceManager(models.Manager):

    @transaction.atomic
    def get_or_create_from_ob2(self, badgeclass, assertion_obo, recipient_identifier, source=None, original_json=None):
        image_url = assertion_obo.get('image', None)
        image = None
        if image_url is None:
            image = badgeclass.image.file
        else:
            image = _fetch_image_and_get_file(image_url, upload_to='remote/assertion')

        badgeinstance, created = self.get_or_create(
            source_url=assertion_obo.get('id'),
            defaults=dict(
                recipient_identifier=recipient_identifier,
                source=source if source is not None else 'local',
                original_json=original_json,
                badgeclass=badgeclass,
                issuer=badgeclass.cached_issuer,
                image=image,
                acceptance=self.model.ACCEPTANCE_ACCEPTED,
                narrative=assertion_obo.get('narrative', None)
            )
        )
        if created:
            evidence = assertion_obo.get('evidence', None)
            if evidence:
                from issuer.models import BadgeInstanceEvidence
                if isinstance(evidence, basestring):
                    # we got a single iri as 'evidence' field
                    BadgeInstanceEvidence.objects.create(
                        badgeinstance=badgeinstance,
                        evidence_url=evidence
                    )
                else:
                    for evidence_item in evidence:
                        badgeinstanceevidence = BadgeInstanceEvidence.objects.create_from_ob2(badgeinstance, evidence_item)
        return badgeinstance, created

    def create_badgeinstance(
            self, badgeclass, recipient_id, narrative=None, evidence=None,
            notify=False, check_completions=True,
            allow_uppercase=False, badgr_app=None, **kwargs
    ):
        """
        Convenience method to award a badge to a recipient_id
        :param allow_uppercase: bool
        :type badgeclass: BadgeClass
        :type recipient_id: str
        :type issuer: Issuer
        :type notify: bool
        :type check_completions: bool
        :type evidence: list of dicts(url=string, narrative=string)
        """
        recipient_identifier = recipient_id if allow_uppercase else recipient_id.lower()

        new_instance = self.model(
            badgeclass=badgeclass,
			issuer=badgeclass.issuer,
            recipient_identifier=recipient_identifier,
			narrative=narrative,
			**kwargs
        )

        with transaction.atomic():
            new_instance.save()

            if evidence is not None:
                from issuer.models import BadgeInstanceEvidence
                for evidence_obj in evidence:
                    evidence_url = evidence_obj.get('evidence_url')
                    narrative = evidence_obj.get('narrative')
                    new_evidence = BadgeInstanceEvidence(badgeinstance=new_instance, evidence_url=evidence_url)
                    if narrative:
                        new_evidence.narrative = narrative
                    new_evidence.save()

        if check_completions:
            award_badges_for_pathway_completion.delay(badgeinstance_pk=new_instance.pk)

        if notify:
            new_instance.notify_earner(badgr_app=badgr_app)

        return new_instance

