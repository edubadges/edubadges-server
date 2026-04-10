import os
from django.core.checks import register, Warning

@register()
def check_firebase_json_file(app_configs, **kwargs):
    """
    Check that the Firebase service account JSON file exists.
    """
    json_file = os.environ.get("FIREBASE_JSON_FILE")
    if not json_file:
        return [
            Warning(
                "FIREBASE_JSON_FILE environment variable not set.",
                hint="Set FIREBASE_JSON_FILE to the path of your Firebase service account JSON file.",
                id="fcm_django.W001",
            )
        ]
    if not os.path.exists(json_file):
        return [
            Warning(
                f"Firebase service account JSON file not found at {json_file}",
                hint="Make sure the file exists and the Django process can read it.",
                id="fcm_django.W002",
            )
        ]
    return []
