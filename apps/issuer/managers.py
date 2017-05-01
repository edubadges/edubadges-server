# encoding: utf-8
from __future__ import unicode_literals

from django.db import models, transaction

from pathway.tasks import award_badges_for_pathway_completion


class BadgeInstanceManager(models.Manager):
    def create_badgeinstance(
            self, badgeclass, recipient_id, evidence=None,
            notify=False, check_completions=True, created_by=None,
            allow_uppercase=False, badgr_app=None,
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
            badgeclass=badgeclass, issuer=badgeclass.issuer,
            recipient_identifier=recipient_identifier,
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
            award_badges_for_pathway_completion.delay(new_instance.slug)

        if notify:
            new_instance.notify_earner(badgr_app=badgr_app)

        return new_instance

