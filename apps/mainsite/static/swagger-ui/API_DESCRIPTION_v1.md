## Authentication

Authenticate requests by including an Authorization header.  For example:

```bash
curl 'https://api.badgr.io/v1/user/profile' -H "Authorization: Token <auth token>"
```

# Generate Auth Token
To retrieve an auth token, POST a username/password combination to /api-auth/token.  For example:

```bash
curl -X POST 'https://api.badgr.io/api-auth/token' -d "username=YOUREMAIL&password=YOURPASSWORD"
```
