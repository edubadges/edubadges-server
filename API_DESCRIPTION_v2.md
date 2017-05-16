## Authentication

Authentication is performed using the HTTP Basic Auth scheme.  Authenticate requests by including an Authorization header.  For example:

```bash
curl https://api.badgr.io/v2/user/profile -H "Authorization: Token Wi3U7IMRxSXwvBH9m5x6NlEFdtd3CsJBsTHfYKFO7mI="
```

# Generate Auth Token
To retrieve an auth token, POST a username/password combination to /api-auth/token.  For example:

```bash
curl -X POST https://api.badgr.io/api-auth/token/ '{"username": "XXX", "password": "YYY"}'
```

## Content-Type
Unless otherwise noted, all requests and responses MUST use the application/json Content-Type.

The API does NOT support application/x-www-form-urlencoded or multipart/form-data.

## Response Envelope

Success responses from the /v2/ API come in three basic forms, shown below:

# Basic Response
```json
{
  "status": {
    "success": true,
    "description": "ok"
  },
  "result": [
    { /* single entry */}
  ]
}
```

# List Response
```json
{
  "status": {
    "success": true,
    "description": "ok"
  },
  "result": [
    {/* entry */},
    {/* entry */},
    ...
  ]
}
```

Unless otherwise documented, list responses SHOULD contain entities of a single type.

# List Response (Paginated)
```json
{
  "status": {
    "success": true,
   "description": "ok"
  },
  "result": [
    {/* entry */},
    {/* entry */},
    ..
  ],
  "pagination": 
    "hasNext": true,
    "nextResult": "https://api.badgr.io/v2/endpoint?token=XXX",
    "nextToken": "XXX",
    "hasPrevious": false,
    "previousResult": "https://api.badgr.io/v2/endpoint?token=YYY",
    "previousToken": "YYY
  }
}
```

Unless otherwise documented, paginated list responses SHOULD contain entities of a single type.