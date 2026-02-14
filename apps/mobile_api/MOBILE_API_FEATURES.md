# Mobile API Enhancements: Analytics Tracking & Rate Limiting

## Overview

This document describes two new features implemented for the mobile API:

1. **Analytics Tracking** - Comprehensive request logging and usage analytics
2. **Rate Limiting** - Per-device rate limiting to prevent abuse

## Feature 1: Analytics Tracking

### Implementation

The analytics tracking system automatically logs all mobile API requests and provides insights into:

- **Request metrics**: Method, endpoint, status code, response time
- **Device information**: Device ID, type, model, app version, OS version  
- **User information**: Associated user (when authenticated)
- **Client information**: IP address, user agent
- **Timestamps**: When each request occurred

### Database Models

#### `MobileDevice`

Stores information about mobile devices:

```python
- id: UUID (primary key)
- device_id: Unique device identifier (string, unique)
- device_type: Type of device (iOS/Android)
- device_model: Device model
- app_version: App version
- os_version: Operating system version
- created_at: When device was first seen
- last_seen: When device was last active
```

#### `MobileAPIRequestLog`

Stores detailed request logs:

```python
- id: Auto-incrementing ID
- device: ForeignKey to MobileDevice
- user: ForeignKey to User (optional)
- endpoint: API endpoint called
- method: HTTP method (GET, POST, etc.)
- status_code: HTTP response status code
- response_time_ms: Response time in milliseconds
- timestamp: When request occurred
- ip_address: Client IP address
- user_agent: User agent string
```

### How It Works

1. **Middleware-based tracking**: `MobileAPIAnalyticsMiddleware` automatically logs all mobile API requests
2. **Device identification**: Uses `X-Device-ID` header to identify devices
3. **Performance measurement**: Tracks response times automatically
4. **Admin interface**: Django admin provides full access to analytics data

### Required Headers

For full analytics tracking, mobile clients should send these headers:

```
X-Device-ID: unique-device-identifier
X-Device-Type: iOS|Android
X-Device-Model: iPhone 13|Samsung Galaxy S22
X-App-Version: 1.2.3
X-OS-Version: 15.4|12
```

### Analytics Endpoints

#### `GET /mobile/api/analytics-summary`

Get summary statistics for mobile API usage:

**Response:**
```json
{
    "time_range": "last_24_hours",
    "total_requests": 100,
    "unique_devices": 10,
    "active_users": 5,
    "endpoints": {
        "/mobile/api/login": 40,
        "/mobile/api/badge-instances": 30,
        "/mobile/api/test-analytics": 30
    }
}
```

#### `GET /mobile/api/test-analytics`

Test endpoint to verify analytics tracking is working:

**Response:**
```json
{
    "message": "Analytics tracking is working",
    "device_detected": true,
    "device_id": "abc123-def456",
    "user_agent": "MobileApp/1.0 (iPhone; iOS 15.4)"
}
```

### Admin Interface

Access analytics data through Django admin:
- `/admin/mobile_api/mobiledevice/` - View all registered devices
- `/admin/mobile_api/mobileapirequestlog/` - View all request logs

### Performance Considerations

- **Indexing**: All frequently queried fields are indexed
- **Caching**: Analytics summaries can be cached for performance
- **Data retention**: Consider implementing data retention policies for long-term storage

## Feature 2: Rate Limiting

### Implementation

Per-device rate limiting prevents API abuse while allowing legitimate usage:

- **Cache-based**: Uses Django's cache framework (Redis recommended)
- **Device-specific**: Limits are applied per device ID
- **Endpoint-specific**: Different endpoints can have different limits
- **Flexible configuration**: Supports various time windows (second, minute, hour, day)

### Rate Limiter Configuration

Default rate limit: **100 requests per hour per device**

Custom limits can be specified per endpoint using the `mobile_api_rate_limit` attribute on the request object.

### How It Works

1. **Middleware-based enforcement**: `MobileAPIRateLimitMiddleware` checks limits before processing requests
2. **Device identification**: Uses `X-Device-ID` header to identify devices
3. **Cache storage**: Uses Django cache to store request counts
4. **Automatic cleanup**: Cache entries expire automatically

### Rate Limit Headers

Clients should include:

```
X-Device-ID: unique-device-identifier
```

If no device ID is provided, a temporary one is generated for the session.

### Rate Limit Endpoints

#### `GET /mobile/api/test-rate-limit`

Test endpoint to verify rate limiting is working:

**Normal Response (under limit):**
```json
{
    "message": "Request allowed",
    "device_id": "test-device",
    "endpoint": "/mobile/api/test-rate-limit"
}
```

**Rate Limited Response (over limit):**
```json
{
    "error": "rate_limit_exceeded",
    "message": "API rate limit exceeded",
    "retry_after": 3600
}
```

Status Code: `429 Too Many Requests`

### Custom Rate Limits

To set custom rate limits for specific endpoints, you can:

1. **Decorate views**: Add rate limit metadata to views
2. **Middleware configuration**: Configure different limits for different endpoint patterns
3. **Dynamic limits**: Implement logic to adjust limits based on user tier or other factors

### Rate Limit Examples

```python
# 10 requests per minute
"10/minute"

# 100 requests per hour (default)
"100/hour"

# 1000 requests per day
"1000/day"

# 5 requests per second
"5/second"
```

## Integration Guide

### Mobile Client Integration

#### iOS (Swift)

```swift
var request = URLRequest(url: URL(string: "https://api.example.com/mobile/api/badge-instances")!)
request.setValue("Bearer YOUR_ACCESS_TOKEN", forHTTPHeaderField: "Authorization")
request.setValue("mobile", forHTTPHeaderField: "X-Requested-With")
request.setValue(UIDevice.current.identifierForVendor?.uuidString, forHTTPHeaderField: "X-Device-ID")
request.setValue("iOS", forHTTPHeaderField: "X-Device-Type")
request.setValue(UIDevice.current.model, forHTTPHeaderField: "X-Device-Model")
request.setValue(Bundle.main.infoDictionary?["CFBundleShortVersionString"] as? String, forHTTPHeaderField: "X-App-Version")
request.setValue(UIDevice.current.systemVersion, forHTTPHeaderField: "X-OS-Version")
```

#### Android (Kotlin)

```kotlin
val client = OkHttpClient()
val request = Request.Builder()
    .url("https://api.example.com/mobile/api/badge-instances")
    .addHeader("Authorization", "Bearer YOUR_ACCESS_TOKEN")
    .addHeader("X-Requested-With", "mobile")
    .addHeader("X-Device-ID", Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID))
    .addHeader("X-Device-Type", "Android")
    .addHeader("X-Device-Model", Build.MODEL)
    .addHeader("X-App-Version", BuildConfig.VERSION_NAME)
    .addHeader("X-OS-Version", Build.VERSION.RELEASE)
    .build()
```

### Error Handling

#### Rate Limit Errors

```javascript
// JavaScript example
fetch('/mobile/api/test-rate-limit', {
    headers: {
        'Authorization': 'Bearer YOUR_TOKEN',
        'X-Requested-With': 'mobile',
        'X-Device-ID': 'device-123'
    }
})
.then(response => {
    if (response.status === 429) {
        return response.json().then(data => {
            console.log('Rate limited. Retry after:', data.retry_after, 'seconds');
            // Implement exponential backoff or notify user
        });
    }
    return response.json();
})
.catch(error => {
    console.error('API error:', error);
});
```

### Monitoring and Alerts

#### Django Admin

- Monitor device registrations and growth
- Track API usage patterns
- Identify problematic devices or users

#### Custom Alerts

Implement custom alerts for:
- Sudden spikes in API usage
- Unusual device activity
- High error rates

## Deployment Considerations

### Database

- **Indexing**: Ensure all indexes are created (handled by migrations)
- **Performance**: Consider partitioning large request log tables
- **Retention**: Implement data retention policies for analytics data

### Caching

- **Redis recommended**: For best performance with rate limiting
- **Cache timeout**: Configure appropriate cache timeouts
- **Memory**: Ensure sufficient cache memory for rate limit tracking

### Scaling

- **Horizontal scaling**: Middleware is stateless and works in distributed environments
- **Database sharding**: Consider sharding for very high volume analytics
- **Read replicas**: Use read replicas for analytics queries

## Testing

### Test Endpoints

Three test endpoints are provided:

1. **`/mobile/api/test-analytics`** - Test analytics tracking
2. **`/mobile/api/test-rate-limit`** - Test rate limiting  
3. **`/mobile/api/analytics-summary`** - Get analytics summary

### Test Script

```bash
# Test analytics tracking
curl -H "X-Requested-With: mobile" \
     -H "X-Device-ID: test-device-123" \
     -H "X-Device-Type: iOS" \
     -H "X-App-Version: 1.0.0" \
     http://localhost:8000/mobile/api/test-analytics

# Test rate limiting (run multiple times to trigger limit)
for i in {1..15}; do
    curl -H "X-Requested-With: mobile" \
         -H "X-Device-ID: test-device-456" \
         http://localhost:8000/mobile/api/test-rate-limit
    echo ""
done

# Get analytics summary
curl -H "X-Requested-With: mobile" \
     http://localhost:8000/mobile/api/analytics-summary
```

## Security Considerations

### Data Privacy

- **Device IDs**: Should be hashed or anonymized if storing long-term
- **IP addresses**: Consider privacy regulations (GDPR, etc.)
- **User agent**: May contain sensitive information

### Rate Limit Security

- **Device spoofing**: Implement additional protections against device ID spoofing
- **DDoS protection**: Rate limiting helps but should be part of broader DDoS strategy
- **API keys**: Consider requiring API keys for sensitive endpoints

## Future Enhancements

### Analytics Enhancements

- **Real-time dashboard**: Web interface for viewing analytics
- **Export functionality**: CSV/Excel export of analytics data
- **Advanced filtering**: More sophisticated query capabilities
- **Trends and predictions**: Machine learning for usage patterns

### Rate Limiting Enhancements

- **Tiered limits**: Different limits for different user tiers
- **Burst capacity**: Allow short bursts above normal limits
- **IP-based fallback**: Fallback to IP-based limiting when device ID unavailable
- **Endpoint grouping**: Group endpoints for shared limits

### Additional Features

- **Device management**: Allow users to manage registered devices
- **Push notifications**: Integrate with existing FCM push notification system
- **Usage alerts**: Notify users when approaching limits
- **API health monitoring**: Track endpoint response times and error rates

## Troubleshooting

### Analytics Not Working

1. **Check middleware**: Ensure `MobileAPIAnalyticsMiddleware` is in `MIDDLEWARE`
2. **Verify headers**: Mobile client must send `X-Requested-With: mobile`
3. **Database**: Check that tables were created successfully
4. **Permissions**: Ensure middleware has database write permissions

### Rate Limiting Not Working

1. **Check middleware**: Ensure `MobileAPIRateLimitMiddleware` is in `MIDDLEWARE`
2. **Cache configuration**: Verify Django cache is properly configured
3. **Middleware order**: Rate limit middleware should come before analytics middleware
4. **Device ID**: Ensure device ID is being sent in headers

### Performance Issues

1. **Database indexing**: Verify all indexes are created
2. **Cache performance**: Monitor cache hit/miss ratios
3. **Query optimization**: Check for slow database queries
4. **Batch processing**: Consider batch processing for analytics aggregation

## Support

For issues with the mobile API enhancements:

1. Check Django logs for errors
2. Verify database tables exist
3. Test with curl or Postman
4. Review middleware configuration
5. Check cache backend status

## Changelog

### Version 1.0 (2026-02-14)

- Initial implementation of analytics tracking
- Per-device rate limiting
- Admin interface for analytics
- Test endpoints for verification
- Comprehensive documentation