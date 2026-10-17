"""
Settings shared by every environment.

Environment-specific settings (database, storage backend, security flags)
live in dev.py and prod.py, per the Development Guide's recommendation to
keep local development simple (SQLite + local media/) while designing
things so the production upgrade (PostgreSQL + private object storage) is
a settings change, not a rewrite. See Sections 8, 11 and 20 of the guide.
"""
from pathlib import Path

from decouple import Csv, config

# Build paths inside the project like this: BASE_DIR / "subdir".
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="django-insecure-change-me-in-.env")

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
]

LOCAL_APPS = [
    "accounts",
    "dashboard",
    "folders",
    "notes",
    "storage_app",
    "search_app",
    "archive_app",
    "audit",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "dashboard.context_processors.storage_summary",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ---------------------------------------------------------------------------
# Password validation
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# Authentication (Section 8: "Django built-in authentication")
# ---------------------------------------------------------------------------
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

# ---------------------------------------------------------------------------
# Internationalization
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Application-specific settings (Section 25.4 of the guide)
# ---------------------------------------------------------------------------
MAX_UPLOAD_SIZE_MB = config("MAX_UPLOAD_SIZE_MB", default=250, cast=int)
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024

ALLOWED_FILE_EXTENSIONS = config(
    "ALLOWED_FILE_EXTENSIONS",
    default=".jpg,.jpeg,.png,.gif,.webp,.mp4,.mov,.mp3,.wav,.pdf,.doc,.docx,"
    ".xls,.xlsx,.ppt,.pptx,.txt,.csv,.zip",
    cast=Csv(),
)

RECYCLE_BIN_RETENTION_DAYS = config("RECYCLE_BIN_RETENTION_DAYS", default=30, cast=int)

# Storage quota shown on the dashboard (Section 4: "Show total, used and
# available storage"). Purely informational in V1 -- uploads are not
# actually blocked once this is exceeded, but the UI warns the user.
DEFAULT_USER_QUOTA_GB = config("DEFAULT_USER_QUOTA_GB", default=5, cast=int)
DEFAULT_USER_QUOTA_BYTES = DEFAULT_USER_QUOTA_GB * 1024 * 1024 * 1024

# Django enforces this at the request level as a second line of defense
# on top of the per-file ALLOWED_FILE_EXTENSIONS / MAX_UPLOAD_SIZE_MB checks
# implemented in storage_app.forms.
DATA_UPLOAD_MAX_MEMORY_SIZE = MAX_UPLOAD_SIZE_BYTES
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # spool >5MB to disk instead of RAM
