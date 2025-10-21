# S3/MinIO Storage Configuration

This document describes how to configure and use S3 or MinIO storage for BadgeClass images and other file uploads in the edubadges-server.

## Overview

The application now supports storing uploaded files (BadgeClass images, Issuer images, etc.) in S3-compatible storage systems including:
- Amazon S3
- MinIO
- Other S3-compatible storage services

## Configuration

### Environment Variables

Set the following environment variables to enable S3 storage:

#### Required Variables
```bash
AWS_ACCESS_KEY_ID=your_access_key_id
AWS_SECRET_ACCESS_KEY=your_secret_access_key
AWS_STORAGE_BUCKET_NAME=your_bucket_name
```

#### Optional Variables
```bash
# For MinIO or custom S3 endpoint
AWS_S3_ENDPOINT_URL=http://your-minio-host:9000

# AWS region (default: us-east-1)
AWS_S3_REGION_NAME=us-east-1

# SSL settings (default: true)
AWS_S3_USE_SSL=true

# Signature version (default: s3v4)
AWS_S3_SIGNATURE_VERSION=s3v4

# Custom domain for file URLs (optional)
AWS_S3_CUSTOM_DOMAIN=cdn.yourdomain.com
```

### MinIO Configuration Example

For a MinIO setup:
```bash
AWS_ACCESS_KEY_ID=minioadmin
AWS_SECRET_ACCESS_KEY=minioadmin
AWS_STORAGE_BUCKET_NAME=edubadges
AWS_S3_ENDPOINT_URL=http://minio:9000
AWS_S3_USE_SSL=false
AWS_S3_REGION_NAME=us-east-1
```

### AWS S3 Configuration Example

For AWS S3:
```bash
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=my-edubadges-bucket
AWS_S3_REGION_NAME=eu-west-1
```

## Installation

The required dependencies are already included in `requirements.txt`:

```
django-storages[s3]==1.7
boto3==1.34.162
```

Install them with:
```bash
pip install -r requirements.txt
```

## Testing the Configuration

Use the management command to test your S3 configuration:

```bash
python manage.py test_s3_storage
```

This command will:
- Check if S3 is enabled
- Test file upload/download
- Verify URL generation
- Test with existing BadgeClass models

## Migration from Local Storage

If you have existing files stored locally, use the migration command:

```bash
# Dry run to see what would be migrated
python manage.py migrate_images_to_s3 --dry-run

# Migrate all images
python manage.py migrate_images_to_s3

# Migrate only BadgeClass images
python manage.py migrate_images_to_s3 --model badgeclass

# Migrate only BadgeInstance images  
python manage.py migrate_images_to_s3 --model badgeinstance
```

## File Structure in S3

Files will be stored in S3 with the following structure:
```
bucket/
├── uploads/
│   ├── badges/           # BadgeClass and BadgeInstance images
│   ├── issuers/          # Issuer images (English/Dutch)
│   ├── institution/      # Institution images
│   └── faculties/        # Faculty images
├── remote/
│   ├── badgeclass/       # Imported BadgeClass images
│   ├── issuer/           # Imported Issuer images
│   └── assertion/        # Imported BadgeInstance images
└── baked/                # Baked badge images
    └── {version}/
```

## Security and Permissions

### Bucket Policy

The S3 bucket should have appropriate permissions. For public read access to badge images, you can use this bucket policy:

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::your-bucket-name/*"
        }
    ]
}
```

### IAM Permissions

The AWS user/role needs these permissions:
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
                "s3:PutObject",
                "s3:DeleteObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::your-bucket-name",
                "arn:aws:s3:::your-bucket-name/*"
            ]
        }
    ]
}
```

## Troubleshooting

### Common Issues

1. **Connection errors**: Check your endpoint URL and credentials
2. **Permission errors**: Verify bucket policies and IAM permissions
3. **SSL errors**: For MinIO, ensure `AWS_S3_USE_SSL=false` if using HTTP
4. **URL generation issues**: Check `AWS_S3_CUSTOM_DOMAIN` setting

### Debug Commands

```bash
# Test S3 connection and configuration
python manage.py test_s3_storage

# Check if files exist in storage
python manage.py shell
>>> from django.core.files.storage import default_storage
>>> default_storage.exists('uploads/badges/test.png')
>>> default_storage.url('uploads/badges/test.png')
```

### Logs

Enable debug logging to see S3 operations:
```python
LOGGING = {
    'loggers': {
        'boto3': {
            'level': 'DEBUG',
        },
        'botocore': {
            'level': 'DEBUG',
        },
    }
}
```

## Performance Considerations

- Files are cached with `CacheControl: max-age=86400` (24 hours)
- Consider using CloudFront or similar CDN for better performance
- Monitor S3 costs, especially for GET requests

## Backup and Recovery

- S3 provides high durability (99.999999999%)
- Consider enabling versioning on your S3 bucket
- Set up cross-region replication for critical data
- Regular backups to a separate storage location recommended