from django.utils.deconstruct import deconstructible
from storages.backends.s3boto3 import S3Boto3Storage
from typing import Optional

from mainsite import settings


@deconstructible
class ProxiedS3Storage(S3Boto3Storage):
    def url(
        self, name: str, parameters: Optional[dict[str, str]] = None, expire: Optional[int] = None, proxied: bool = True
    ) -> Optional[str]:
        """
        Override the url method to proxy requests to the proxied S3 storage through Django, so
        that Django can handle the authentication and authorization based on the users' access permissions
        for the resource that holds the file.
        Set proxed to False if you want to access the file directly from the s3
        backend. Default is True, so the file is accessed through Django's
        authentication and authorization.
        """
        if proxied:
            return getattr(settings, 'HTTP_ORIGIN') + getattr(settings, 'MEDIA_URL') + name

        return super().url(name, parameters, expire)
