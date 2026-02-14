import time
import uuid
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from .models import MobileDevice, MobileAPIAnalytics, MobileAPIRateLimiter


class MobileAPIAnalyticsMiddleware:
    """
    Middleware to track analytics for mobile API requests
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process mobile API requests
        if not getattr(request, 'mobile_api_call', False):
            return self.get_response(request)

        # Store start time for response time calculation
        request._analytics_start_time = timezone.now()

        # Get device information from headers
        device_id = request.headers.get('X-Device-ID')
        device_type = request.headers.get('X-Device-Type')
        device_model = request.headers.get('X-Device-Model')
        app_version = request.headers.get('X-App-Version')
        os_version = request.headers.get('X-OS-Version')

        # Get or create device record
        device = None
        if device_id:
            device, created = MobileDevice.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'device_type': device_type,
                    'device_model': device_model,
                    'app_version': app_version,
                    'os_version': os_version,
                },
            )

            # Update device info if it changed
            if not created and device:
                update_needed = False
                if device_type and device.device_type != device_type:
                    device.device_type = device_type
                    update_needed = True
                if device_model and device.device_model != device_model:
                    device.device_model = device_model
                    update_needed = True
                if app_version and device.app_version != app_version:
                    device.app_version = app_version
                    update_needed = True
                if os_version and device.os_version != os_version:
                    device.os_version = os_version
                    update_needed = True

                if update_needed:
                    device.last_seen = timezone.now()
                    device.save()

        # Store device in request for later use
        request.mobile_device = device

        # Process the request
        response = self.get_response(request)

        # Log the request for analytics
        MobileAPIAnalytics.log_request(request, response, device)

        return response


class MobileAPIRateLimitMiddleware:
    """
    Middleware to enforce rate limiting for mobile API requests
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only process mobile API requests
        if not getattr(request, 'mobile_api_call', False):
            return self.get_response(request)

        # Get device ID from headers
        device_id = request.headers.get('X-Device-ID')

        # If no device ID, generate a temporary one for this session
        if not device_id:
            device_id = str(uuid.uuid4())

        # Check rate limiting
        endpoint = request.path
        rate_limit_str = getattr(request, 'mobile_api_rate_limit', None)

        is_limited, retry_after = MobileAPIRateLimiter.is_rate_limited(device_id, endpoint, rate_limit_str)

        if is_limited:
            return JsonResponse(
                {'error': 'rate_limit_exceeded', 'message': 'API rate limit exceeded', 'retry_after': retry_after},
                status=429,
            )

        return self.get_response(request)
