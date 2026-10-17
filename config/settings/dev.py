"""
Version 1 / local development settings.

SQLite for the database, the local media/ folder for file storage --
exactly the "Best starting stack" described in Section 26 of the
Development Guide: Python + Django + HTML/Bootstrap/JS + SQLite +
Django media folder. No cloud credentials are required to run this.
"""
from decouple import Csv, config

from .base import *  # noqa: F401,F403
from .base import BASE_DIR

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="127.0.0.1,localhost", cast=Csv())

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# --- Local file storage (Section 11.1) ---
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relaxed for local HTTP development; prod.py tightens all of these.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
