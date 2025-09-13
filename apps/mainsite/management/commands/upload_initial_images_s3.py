from django.core.management.base import BaseCommand
from mainsite.seeds.util import upload_initial_images_to_s3


class Command(BaseCommand):
    help = 'Upload initial PNG images to S3 storage for seeding'

    def handle(self, *args, **options):
        self.stdout.write("Starting upload of initial images to S3...")
        upload_initial_images_to_s3()
        self.stdout.write(
            self.style.SUCCESS("Initial image upload process completed.")
        )