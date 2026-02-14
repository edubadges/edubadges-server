from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .models import MobileAPIAnalytics, MobileAPIRateLimiter


class TestAnalyticsAPI(APIView):
    """
    Test endpoint to demonstrate analytics tracking
    """

    permission_classes = (AllowAny,)

    @extend_schema(
        description='Test endpoint for analytics tracking',
        responses={
            200: OpenApiResponse(
                description='Analytics test successful',
                examples=[
                    OpenApiExample(
                        'Analytics Test',
                        value={'message': 'Analytics tracking is working', 'device_detected': True},
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        Test analytics tracking - this endpoint will automatically log the request
        if called from a mobile device with proper headers.
        """
        device_id = request.headers.get('X-Device-ID')
        device_detected = bool(device_id)

        return Response(
            {
                'message': 'Analytics tracking is working',
                'device_detected': device_detected,
                'device_id': device_id if device_id else None,
                'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
            }
        )


class TestRateLimitAPI(APIView):
    """
    Test endpoint to demonstrate rate limiting
    """

    permission_classes = (AllowAny,)

    @extend_schema(
        description='Test endpoint for rate limiting',
        responses={
            200: OpenApiResponse(
                description='Rate limit test successful',
                examples=[
                    OpenApiExample(
                        'Rate Limit Test',
                        value={'message': 'Request allowed', 'remaining_requests': 99},
                        response_only=True,
                    ),
                ],
            ),
            429: OpenApiResponse(
                description='Rate limit exceeded',
                examples=[
                    OpenApiExample(
                        'Rate Limit Exceeded',
                        value={
                            'error': 'rate_limit_exceeded',
                            'message': 'API rate limit exceeded',
                            'retry_after': 3600,
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        Test rate limiting - this endpoint demonstrates per-device rate limiting
        """
        device_id = request.headers.get('X-Device-ID', 'test-device')
        endpoint = request.path

        # Check rate limiting (10 requests per minute for testing)
        is_limited, retry_after = MobileAPIRateLimiter.is_rate_limited(device_id, endpoint, '10/minute')

        if is_limited:
            return Response(
                {'error': 'rate_limit_exceeded', 'message': 'API rate limit exceeded', 'retry_after': retry_after},
                status=429,
            )

        return Response({'message': 'Request allowed', 'device_id': device_id, 'endpoint': endpoint})


class AnalyticsSummaryAPI(APIView):
    """
    Get analytics summary (admin only)
    """

    permission_classes = (AllowAny,)  # In production, use proper admin permission

    @extend_schema(
        description='Get analytics summary for mobile API',
        responses={
            200: OpenApiResponse(
                description='Analytics summary',
                examples=[
                    OpenApiExample(
                        'Analytics Summary',
                        value={
                            'total_requests': 100,
                            'unique_devices': 10,
                            'active_users': 5,
                            'endpoints': {
                                '/mobile/api/login': 40,
                                '/mobile/api/badge-instances': 30,
                                '/mobile/api/test-analytics': 30,
                            },
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        Get summary of mobile API analytics
        """
        from .models import MobileAPIRequestLog, MobileDevice
        from django.db.models import Count
        from django.utils import timezone
        from datetime import timedelta

        # Time range: last 24 hours
        time_range = timezone.now() - timedelta(days=1)

        # Get statistics
        total_requests = MobileAPIRequestLog.objects.filter(timestamp__gte=time_range).count()
        unique_devices = MobileDevice.objects.filter(last_seen__gte=time_range).count()

        # Get active users (users who made requests in the last 24 hours)
        active_users = (
            MobileAPIRequestLog.objects.filter(timestamp__gte=time_range, user__isnull=False)
            .values('user')
            .distinct()
            .count()
        )

        # Get endpoint statistics
        endpoints = (
            MobileAPIRequestLog.objects.filter(timestamp__gte=time_range)
            .values('endpoint')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        endpoint_stats = {item['endpoint']: item['count'] for item in endpoints}

        return Response(
            {
                'time_range': 'last_24_hours',
                'total_requests': total_requests,
                'unique_devices': unique_devices,
                'active_users': active_users,
                'endpoints': endpoint_stats,
            }
        )
