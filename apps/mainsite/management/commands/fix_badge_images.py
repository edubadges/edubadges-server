from django.core.management.base import BaseCommand

from composition.models import LocalBadgeInstance


class Command(BaseCommand):
    args = ''
    help = 'Upgrades instances if image URLs had been mis-set'

    def handle(self, *args, **options):
        """
        Ensures that LocalBadgeInstance image references are properly generated.
        """
        instances = LocalBadgeInstance.objects.all()

        for instance in instances:
            if instance.json['image'] != instance.image_url():
                instance.json['image'] = instance.image_url()
                instance.save()
