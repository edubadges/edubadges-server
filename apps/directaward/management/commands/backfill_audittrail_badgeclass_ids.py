from django.core.management.base import BaseCommand
from django.db import transaction

from directaward.models import DirectAwardAuditTrail


class Command(BaseCommand):
    help = "Backfill badgeclass FK on DirectAwardAuditTrail using direct_award.badgeclass"

    def handle(self, *args, **options):
        qs = (
            DirectAwardAuditTrail.objects
            .filter(badgeclass__isnull=True, direct_award__isnull=False)
            .select_related('direct_award__badgeclass')
        )

        total = qs.count()
        self.stdout.write(f"Found {total} audit trail records to backfill")

        updated = 0

        with transaction.atomic():
            for audit in qs.iterator(chunk_size=500):
                badgeclass = audit.direct_award.badgeclass
                if badgeclass is None:
                    continue

                audit.badgeclass = badgeclass
                audit.save(update_fields=['badgeclass'])
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"Successfully backfilled {updated} audit trail records")
        )
