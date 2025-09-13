import os
from django.core.management.base import BaseCommand
from django.core.files.storage import default_storage
from django.conf import settings
from issuer.models import BadgeClass, BadgeInstance, Issuer
from institution.models import Institution, Faculty


class Command(BaseCommand):
    help = 'Migrate existing images from local storage to S3/MinIO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually moving files',
        )
        parser.add_argument(
            '--model',
            type=str,
            choices=['badgeclass', 'badgeinstance', 'issuer', 'institution', 'faculty', 'all'],
            default='all',
            help='Which model to migrate images for',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        model_type = options['model']
        
        if not getattr(settings, 'USE_S3', False):
            self.stdout.write(
                self.style.ERROR("S3 storage is not enabled. Set USE_S3=true in environment.")
            )
            return
        
        self.stdout.write(f"{'DRY RUN: ' if dry_run else ''}Migrating images to S3/MinIO...")
        
        total_migrated = 0
        
        if model_type in ['badgeclass', 'all']:
            total_migrated += self.migrate_badgeclass_images(dry_run)
        
        if model_type in ['badgeinstance', 'all']:
            total_migrated += self.migrate_badgeinstance_images(dry_run)
        
        if model_type in ['issuer', 'all']:
            total_migrated += self.migrate_issuer_images(dry_run)
            
        if model_type in ['institution', 'all']:
            total_migrated += self.migrate_institution_images(dry_run)
            
        if model_type in ['faculty', 'all']:
            total_migrated += self.migrate_faculty_images(dry_run)
        
        self.stdout.write(
            self.style.SUCCESS(f"Migration {'simulation ' if dry_run else ''}completed. {total_migrated} images processed.")
        )

    def migrate_badgeclass_images(self, dry_run=False):
        """Migrate BadgeClass images"""
        self.stdout.write("Migrating BadgeClass images...")
        count = 0
        
        for badge_class in BadgeClass.objects.filter(image__isnull=False):
            if self.migrate_file_field(badge_class, 'image', dry_run):
                count += 1
        
        self.stdout.write(f"BadgeClass images: {count}")
        return count

    def migrate_badgeinstance_images(self, dry_run=False):
        """Migrate BadgeInstance images"""
        self.stdout.write("Migrating BadgeInstance images...")
        count = 0
        
        for badge_instance in BadgeInstance.objects.filter(image__isnull=False):
            if self.migrate_file_field(badge_instance, 'image', dry_run):
                count += 1
        
        self.stdout.write(f"BadgeInstance images: {count}")
        return count

    def migrate_issuer_images(self, dry_run=False):
        """Migrate Issuer images"""
        self.stdout.write("Migrating Issuer images...")
        count = 0
        
        for issuer in Issuer.objects.all():
            if issuer.image_english and self.migrate_file_field(issuer, 'image_english', dry_run):
                count += 1
            if issuer.image_dutch and self.migrate_file_field(issuer, 'image_dutch', dry_run):
                count += 1
        
        self.stdout.write(f"Issuer images: {count}")
        return count

    def migrate_institution_images(self, dry_run=False):
        """Migrate Institution images"""
        self.stdout.write("Migrating Institution images...")
        count = 0
        
        for institution in Institution.objects.all():
            if institution.image_english and self.migrate_file_field(institution, 'image_english', dry_run):
                count += 1
            if institution.image_dutch and self.migrate_file_field(institution, 'image_dutch', dry_run):
                count += 1
        
        self.stdout.write(f"Institution images: {count}")
        return count

    def migrate_faculty_images(self, dry_run=False):
        """Migrate Faculty images"""
        self.stdout.write("Migrating Faculty images...")
        count = 0
        
        for faculty in Faculty.objects.all():
            if faculty.image_english and self.migrate_file_field(faculty, 'image_english', dry_run):
                count += 1
            if faculty.image_dutch and self.migrate_file_field(faculty, 'image_dutch', dry_run):
                count += 1
        
        self.stdout.write(f"Faculty images: {count}")
        return count

    def migrate_file_field(self, obj, field_name, dry_run=False):
        """Migrate a single file field to S3"""
        file_field = getattr(obj, field_name)
        
        if not file_field or not file_field.name:
            return False
            
        try:
            # Check if file is already using S3 storage
            if hasattr(file_field.storage, 'bucket'):
                # Already using S3 storage, skip
                return False
            
            # Check if file exists locally
            local_path = os.path.join(settings.MEDIA_ROOT, file_field.name)
            if not os.path.exists(local_path):
                self.stdout.write(
                    self.style.WARNING(f"Local file not found: {local_path}")
                )
                return False
            
            if dry_run:
                self.stdout.write(f"Would migrate: {file_field.name}")
                return True
            
            # Read the local file
            with open(local_path, 'rb') as local_file:
                file_content = local_file.read()
            
            # Save to S3 with the same path
            s3_path = default_storage.save(file_field.name, file_content)
            
            # Update the file field to point to S3 version
            setattr(obj, field_name, s3_path)
            obj.save(update_fields=[field_name])
            
            self.stdout.write(f"Migrated: {file_field.name} -> {s3_path}")
            return True
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to migrate {obj.__class__.__name__} {obj.id} {field_name}: {str(e)}")
            )
            return False