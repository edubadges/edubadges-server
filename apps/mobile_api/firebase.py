import logging
import os

import firebase_admin

from django.conf import settings

logger = logging.getLogger('Badgr.Debug')


def initialize_firebase():
    firebase_json = getattr(settings, "FIREBASE_JSON_FILE", None)

    if not firebase_json:
        logger.info("Firebase not configured: FIREBASE_JSON_FILE not set")
        return

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = firebase_json

    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
            logger.info("Firebase initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
