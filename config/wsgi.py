"""
WSGI config for the Personal Data Vault project.

Exposes the WSGI callable as a module-level variable named ``application``.
Used by Gunicorn in production (Section 8 / 20 of the Development Guide):

    gunicorn config.wsgi:application --bind 0.0.0.0:8000
"""
import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application = get_wsgi_application()
