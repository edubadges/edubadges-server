

import sys
import os
import semver


__all__ = ['APPS_DIR', 'TOP_DIR', 'get_version']


def get_version(version=None):
    if version is None:
        from .version import VERSION
        version = VERSION
    return semver.format_version(*version)


# assume we are ./apps/mainsite/__init__.py
APPS_DIR = os.path.dirname(os.path.abspath(os.path.dirname(__file__)))
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)

# Path to the whole project (one level up from apps)
TOP_DIR = os.path.dirname(APPS_DIR)

# import the celery app so INSTALLED_APPS gets autodiscovered
from .celery import app as celery_app
