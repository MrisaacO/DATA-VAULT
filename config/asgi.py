"""
ASGI config for the Personal Data Vault project.

Provided so the same project can later be served by Uvicorn/Daphne
(Section 8 of the Development Guide lists "Gunicorn/Uvicorn + Nginx") or
gain async features, without needing to restructure the project.
"""
import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_asgi_application()
