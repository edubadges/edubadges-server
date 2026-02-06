import os

from django.core.checks import register, Warning


@register()
def check_firebase_env_vars(app_configs, **kwargs):
    """
    Check that all required Firebase env variables are set.
    """
    required_vars = [
        "FIREBASE_TYPE",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
    ]

    missing = [var for var in required_vars if not os.environ.get(var)]

    if missing:
        return [
            Warning(
                "Missing Firebase environment variables: {}".format(", ".join(missing)),
                hint="Set these env vars for push notifications to work.",
                id="fcm_django.W001",
            )
        ]
    return []
