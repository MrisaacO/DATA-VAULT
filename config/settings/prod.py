"""
Production settings: PostgreSQL + private S3-compatible object storage,
served over HTTPS with hardened cookies/headers -- the "upgrade" path
described in Sections 8, 12 and 20 of the Development Guide.

Requires the extra packages in requirements-prod.txt:
    pip install -r requirements-prod.txt

Do NOT use this module until:
  * DATABASE_URL points at a real PostgreSQL instance,
  * the OBJECT_STORAGE_* variables point at a private bucket, and
  * the app is actually being served over HTTPS (Section 20 step 5),
otherwise SECURE_SSL_REDIRECT / secure cookies below will lock you out.
"""
import dj_database_url
from decouple import Csv, config

from .base import *  # noqa: F401,F403

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS", cast=Csv())

# WhiteNoise serves compressed, hashed static files straight from Gunicorn
# without needing Nginx to own /static/ (Section 20: "Gunicorn/Uvicorn +
# Nginx"). It must sit directly after SecurityMiddleware.
MIDDLEWARE = list(MIDDLEWARE)
MIDDLEWARE.insert(
    MIDDLEWARE.index("django.middleware.security.SecurityMiddleware") + 1,
    "whitenoise.middleware.WhiteNoiseMiddleware",
)

# --- Database: PostgreSQL (Section 10) ---
DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        ssl_require=config("DATABASE_SSL_REQUIRE", default=True, cast=bool),
    )
}

# --- Object storage: private S3-compatible bucket (Section 11.2 / 12) ---
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_STORAGE_BUCKET_NAME = config("OBJECT_STORAGE_BUCKET")
AWS_S3_REGION_NAME = config("OBJECT_STORAGE_REGION", default="us-east-1")
AWS_S3_ENDPOINT_URL = config("OBJECT_STORAGE_ENDPOINT_URL", default=None) or None
AWS_ACCESS_KEY_ID = config("OBJECT_STORAGE_ACCESS_KEY", default=None) or None
AWS_SECRET_ACCESS_KEY = config("OBJECT_STORAGE_SECRET_KEY", default=None) or None

# Guide Section 12.1/12.2: no public access. Files are only ever reached
# through storage_app.views.file_download / file_preview, which check
# ownership first and then stream the object through Django -- the
# "...or stream the file securely" option Section 16.1 offers as an
# alternative to a redirect-to-signed-URL flow. AWS_QUERYSTRING_AUTH is
# still enabled below so that FileObject.file.url (unused by those two
# views today, but available if you switch to a signed-URL redirect
# later) is a real short-lived presigned link rather than a public one.
AWS_DEFAULT_ACL = None
AWS_QUERYSTRING_AUTH = True
AWS_QUERYSTRING_EXPIRE = 300  # signed URLs expire after 5 minutes
AWS_S3_FILE_OVERWRITE = False

MEDIA_URL = f"https://{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/"

# --- Security hardening (Section 15 / 20 step 1) ---
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"

# Behind Nginx/a load balancer terminating TLS:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --- Logging: send warnings+ to stdout so the deployment platform captures them ---
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "WARNING"},
    "loggers": {
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
