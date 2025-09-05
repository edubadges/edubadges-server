# Health Check Endpoints

This app provides health check endpoints for monitoring and Kubernetes probes.

## Endpoints

### `/health/` - Comprehensive Health Check

Returns detailed JSON status information about the application and its dependencies.

**Response Format:**

```json
{
  "overall_status": "OK",
  "detailed_status": {
    "database_status": "OK"
  }
}
```

**HTTP Status:**

- `200` - Service is healthy
- `503` - Service is unhealthy

### `/health/ready` - Readiness Probe

Simple endpoint for Kubernetes readiness probes. Tests database connectivity to determine if the application is ready to serve requests.

**Response:** Plain text ("Ready" or error message)
**HTTP Status:**

- `200` - Ready to serve requests
- `503` - Not ready (database unavailable)

### `/health/live` - Liveness Probe

Simple endpoint for Kubernetes liveness probes. Always returns 200 if the application process is running.

**Response:** Plain text ("Alive")
**HTTP Status:** Always `200`

## Kubernetes Configuration Examples

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health/ready
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health/live
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```
