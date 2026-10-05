from django.core.management import BaseCommand
from signing.models import AssertionTimeStamp


class Command(BaseCommand):
    def handle(self, *args, **options):
        timestamps = AssertionTimeStamp.objects.filter(proof="")
        for timestamp in timestamps:
            timestamp.update_proof()
