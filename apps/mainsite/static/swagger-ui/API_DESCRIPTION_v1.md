## Authentication

Authenticate requests by including an Authorization header of type "Bearer".  For example:

```bash
curl 'https://api.badgr.io/v1/user/profile' -H "Authorization: Bearer YOURACCESSTOKEN"
```

## Access Tokens
To retrieve an access token, POST a username/password combination to /o/token.  For example:

```bash
curl -X POST 'https://api.badgr.io/o/token' -d "username=YOUREMAIL&password=YOURPASSWORD"
```

returns a response like:
```javascript
{
    "access_token": "YOURACCESSTOKEN", 
    "token_type": "Bearer", 
    "expires_in": 86400, 
    "refresh_token": "YOURREFRESHTOKEN", 
}
```

## Token Expiration
Access tokens will expire, if an expired token is used a 403 status code will be returned.

The refresh token can be used to automatically renew an access token without requiring the password again.  For example:

```bash
curl -X POST 'https://api.badgr.io/o/token' -d "grant_type=refresh_token&refresh_token=YOURREFRESHTOKEN"
```
