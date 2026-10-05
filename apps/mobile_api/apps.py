from django.apps import AppConfig


class MobileApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mobile_api"

    def ready(self):
        # Import your checks module so Django sees it

        # Initialize firebase app
        from .firebase import initialize_firebase  # noqa: PLC0415

        initialize_firebase()
