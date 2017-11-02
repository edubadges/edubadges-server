## Authentication

Authenticate requests by including an Authorization header.  For example:

```bash
curl 'https://api.badgr.io/v2/users/self' -H "Authorization: Token <auth token>"
```

# Generate Auth Token
To retrieve an auth token, POST a username/password combination to /api-auth/token.  For example:

```bash
curl -X POST 'https://api.badgr.io/api-auth/token' -d "username=YOUREMAIL&password=YOURPASSWORD"
```

## Content-Type
Unless otherwise noted, all requests and responses MUST use the application/json Content-Type.
The API does NOT support application/x-www-form-urlencoded or multipart/form-data.

## Response Envelope

```json
{
  "status": {
    "success": true,
    "description": "ok"
  },
  "result": [
    {/* entry */},
    {/* entry */},
  ]
}
```
