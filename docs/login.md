The UI does a `window.location.href` to the server `/account/sociallogin?provider=${service}` where `service` is either eud_id pr surf_conext.

The server endpoint `edubadges-server/apps/badgrsocialauth/views.py` retrieves the `client_id` and `secret` from `socialaccount_socialapp` based
on the provider request argument of the UI redirect and does a redirect to the `eduid/login/`.

 