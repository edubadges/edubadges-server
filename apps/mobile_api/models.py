import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache


class MobileDevice(models.Model):
    """
    Model to track mobile devices for rate limiting and analytics
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device_id = models.CharField(max_length=255, unique=True, help_text='Unique device identifier')
    device_type = models.CharField(max_length=50, null=True, blank=True, help_text='Type of device (iOS/Android)')
    device_model = models.CharField(max_length=100, null=True, blank=True, help_text='Device model')
    app_version = models.CharField(max_length=50, null=True, blank=True, help_text='App version')
    os_version = models.CharField(max_length=50, null=True, blank=True, help_text='Operating system version')
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mobile Device'
        verbose_name_plural = 'Mobile Devices'
        indexes = [
            models.Index(fields=['device_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['last_seen']),
        ]

    def __str__(self):
        return f'{self.device_type or "Unknown"} - {self.device_id[:8]}...'


class MobileAPIRequestLog(models.Model):
    """
    Model to track API requests for analytics
    """

    id = models.BigAutoField(primary_key=True)
    device = models.ForeignKey(
        MobileDevice, on_delete=models.SET_NULL, null=True, blank=True, help_text='Related mobile device'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, help_text='User making the request'
    )
    endpoint = models.CharField(max_length=255, help_text='API endpoint called')
    method = models.CharField(max_length=10, help_text='HTTP method (GET, POST, etc.)')
    status_code = models.IntegerField(help_text='HTTP status code')
    response_time_ms = models.IntegerField(help_text='Response time in milliseconds')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='Client IP address')
    user_agent = models.TextField(null=True, blank=True, help_text='User agent string')

    class Meta:
        verbose_name = 'Mobile API Request Log'
        verbose_name_plural = 'Mobile API Request Logs'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['endpoint']),
            models.Index(fields=['method']),
            models.Index(fields=['status_code']),
            models.Index(fields=['user']),
            models.Index(fields=['device']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.method} {self.endpoint} - {self.status_code}'


class MobileAPIAnalytics:
    """
    Utility class for tracking mobile API analytics
    """

    @classmethod
    def log_request(cls, request, response, device=None):
        """
        Log a mobile API request for analytics
        """
        try:
            # Calculate response time from start time stored in request
            start_time = getattr(request, '_analytics_start_time', None)
            response_time_ms = 0

            if start_time:
                response_time = timezone.now() - start_time
                response_time_ms = int(response_time.total_seconds() * 1000)

            # Get client IP
            ip_address = cls._get_client_ip(request)

            # Create log entry
            MobileAPIRequestLog.objects.create(
                device=device,
                user=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
                endpoint=request.path,
                method=request.method,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],  # Limit to 500 chars
            )
        except Exception as e:
            # Don't let analytics break the application
            if settings.DEBUG:
                print(f'Analytics logging failed: {e}')
            pass

    @classmethod
    def _get_client_ip(cls, request):
        """
        Get the client IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class MobileAPIRateLimiter:
    """
    Rate limiter for mobile API endpoints
    """

    RATE_LIMIT_CACHE_PREFIX = 'mobile_api_rate_limit:'
    DEFAULT_RATE_LIMIT = '100/hour'  # Default: 100 requests per hour per device

    @classmethod
    def parse_rate_limit(cls, rate_limit_str):
        """
        Parse rate limit string like '100/hour' or '10/minute'
        Returns (limit, period_seconds)
        """
        if not rate_limit_str:
            rate_limit_str = cls.DEFAULT_RATE_LIMIT

        try:
            limit, period = rate_limit_str.split('/')
            limit = int(limit)

            # Convert period to seconds
            if period == 'second':
                period_seconds = 1
            elif period == 'minute':
                period_seconds = 60
            elif period == 'hour':
                period_seconds = 3600
            elif period == 'day':
                period_seconds = 86400
            else:
                # Default to hour
                period_seconds = 3600

            return limit, period_seconds
        except (ValueError, AttributeError):
            # Fallback to default
            return 100, 3600

    @classmethod
    def get_rate_limit_key(cls, device_id, endpoint):
        """
        Get cache key for rate limiting
        """
        return f'{cls.RATE_LIMIT_CACHE_PREFIX}{device_id}:{endpoint}'

    @classmethod
    def is_rate_limited(cls, device_id, endpoint, rate_limit_str=None):
        """
        Check if a device is rate limited for a specific endpoint
        Returns (is_limited, retry_after_seconds)
        """
        limit, period_seconds = cls.parse_rate_limit(rate_limit_str)
        cache_key = cls.get_rate_limit_key(device_id, endpoint)

        # Get current count and timestamp
        cache_data = cache.get(cache_key, {'count': 0, 'start_time': timezone.now().timestamp()})

        current_time = timezone.now().timestamp()
        start_time = cache_data['start_time']

        # Reset if period has passed
        if current_time - start_time > period_seconds:
            cache_data = {'count': 1, 'start_time': current_time}
            cache.set(cache_key, cache_data, period_seconds)
            return False, 0

        # Check if limit exceeded
        if cache_data['count'] >= limit:
            retry_after = period_seconds - (current_time - start_time)
            return True, max(0, int(retry_after))

        # Increment count
        cache_data['count'] += 1
        cache.set(cache_key, cache_data, period_seconds)

        return False, 0


# Migration will handle table creation
