# encoding: utf-8
from __future__ import unicode_literals

from django.db import models

from pathway.tasks import award_badges_for_pathway_completion


class BadgeInstanceManager(models.Manager):
    def create_badgeinstance(
            self, badgeclass, recipient_id, evidence_url=None,
            notify=False, check_completions=True, created_by=None,
            allow_uppercase=False, badgr_app=None
    ):
        """
        Convenience method to award a badge to a recipient_id
        :param allow_uppercase: bool
        :type badgeclass: BadgeClass
        :type recipient_id: str
        :type issuer: Issuer
        :type evidence_url: str
        :type notify: bool
        :type check_completions: bool
        """
        recipient_identifier = recipient_id if allow_uppercase else recipient_id.lower()

        new_instance = self.model(
            badgeclass=badgeclass, issuer=badgeclass.issuer,
            recipient_identifier=recipient_identifier,
        )

        if evidence_url:
            new_instance.evidence_url = evidence_url

        new_instance.slug = new_instance.get_new_slug()

        new_instance.save()

        if check_completions:
            award_badges_for_pathway_completion.delay(new_instance.slug)

        if notify:
            new_instance.notify_earner(badgr_app=badgr_app)

        return new_instance

