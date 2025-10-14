#!/bin/sh

# Wait for MinIO to be ready
until mc alias set minio http://minio:9000 minioadmin minioadmin; do
  echo "Waiting for MinIO to be ready..."
  sleep 2
done

echo "MinIO is ready. Starting configuration..."

# Create the edubadges bucket if it doesn't exist
mc mb minio/edubadges --ignore-existing

echo "Bucket 'edubadges' created or already exists."

# Create the edubadges user with access key and secret key
mc admin user add minio edubadges edubadges123

# Create a policy for the edubadges bucket with read-write access
cat > /tmp/edubadges-policy.json <<EOF
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
        "arn:aws:s3:::edubadges",
        "arn:aws:s3:::edubadges/*"
      ]
    }
  ]
}
EOF

# Add the policy
mc admin policy create minio edubadges-policy /tmp/edubadges-policy.json

# Attach the policy to the edubadges user
mc admin policy attach minio edubadges-policy --user=edubadges

echo "User 'edubadges' created with read-write access to 'edubadges' bucket."

# Set the bucket to be publicly readable (optional, adjust based on your needs)
# mc anonymous set download minio/edubadges

echo "MinIO configuration completed successfully!"
