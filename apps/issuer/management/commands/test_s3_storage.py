import tempfile
import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings
from issuer.models import BadgeClass


class Command(BaseCommand):
    help = 'Test S3/MinIO storage functionality for BadgeClass images'

    def handle(self, *args, **options):
        self.stdout.write("Testing S3/MinIO storage configuration...")
        
        # Check if S3 is enabled
        use_s3 = getattr(settings, 'USE_S3', False)
        if use_s3:
            self.stdout.write(
                self.style.SUCCESS("✓ S3 storage is enabled in settings")
            )
            
            # Print S3 configuration
            self.stdout.write(f"Storage backend: {settings.DEFAULT_FILE_STORAGE}")
            self.stdout.write(f"Bucket: {getattr(settings, 'AWS_STORAGE_BUCKET_NAME', 'Not configured')}")
            self.stdout.write(f"Endpoint: {getattr(settings, 'AWS_S3_ENDPOINT_URL', 'Default AWS')}")
            
        else:
            self.stdout.write(
                self.style.WARNING("⚠ S3 storage is disabled. Using local file storage.")
            )
        
        # Test file upload
        self.stdout.write("\nTesting file upload...")
        
        try:
            # Create a simple test image content
            test_content = b"Test image content for S3 storage"
            test_file = ContentFile(test_content, name="test_badge_image.png")
            
            # Save the file using default storage
            file_path = default_storage.save("uploads/badges/test_s3_upload.png", test_file)
            
            self.stdout.write(
                self.style.SUCCESS(f"✓ File uploaded successfully to: {file_path}")
            )
            
            # Test file URL generation
            file_url = default_storage.url(file_path)
            self.stdout.write(f"✓ File URL: {file_url}")
            
            # Test file existence
            if default_storage.exists(file_path):
                self.stdout.write("✓ File exists in storage")
            else:
                self.stdout.write(
                    self.style.ERROR("✗ File does not exist in storage")
                )
            
            # Test file reading
            with default_storage.open(file_path, 'rb') as f:
                content = f.read()
                if content == test_content:
                    self.stdout.write("✓ File content matches")
                else:
                    self.stdout.write(
                        self.style.ERROR("✗ File content does not match")
                    )
            
            # Clean up test file
            default_storage.delete(file_path)
            self.stdout.write("✓ Test file cleaned up")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ File upload test failed: {str(e)}")
            )
        
        # Test with existing BadgeClass model
        self.stdout.write("\nTesting BadgeClass image field...")
        
        try:
            # Create a temporary image file for testing
            test_image_content = b"Fake PNG header for testing purposes"
            test_image_file = ContentFile(test_image_content, name="test_badge_class.png")
            
            # Find the first BadgeClass to test with (without modifying it)
            badge_class = BadgeClass.objects.first()
            
            if badge_class:
                if badge_class.image:
                    self.stdout.write(f"✓ Found BadgeClass with existing image: {badge_class.name}")
                    self.stdout.write(f"  Current image URL: {badge_class.image.url}")
                    self.stdout.write(f"  Image file exists: {badge_class.image.storage.exists(badge_class.image.name)}")
                else:
                    self.stdout.write(f"✓ Found BadgeClass without image: {badge_class.name}")
            else:
                self.stdout.write("⚠ No BadgeClass found for testing")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ BadgeClass test failed: {str(e)}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("\nS3 storage test completed!")
        )
        
        if use_s3:
            self.stdout.write("\nTo use S3 storage, ensure these environment variables are set:")
            self.stdout.write("- USE_S3=true")
            self.stdout.write("- AWS_ACCESS_KEY_ID=your_access_key")
            self.stdout.write("- AWS_SECRET_ACCESS_KEY=your_secret_key")
            self.stdout.write("- AWS_STORAGE_BUCKET_NAME=your_bucket_name")
            self.stdout.write("- AWS_S3_ENDPOINT_URL=http://your-minio-host:9000 (for MinIO)")
            self.stdout.write("- AWS_S3_REGION_NAME=us-east-1 (or your region)")