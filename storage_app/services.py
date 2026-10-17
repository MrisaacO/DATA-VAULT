"""
Helpers for turning an uploaded file into a safely-stored object, per
Section 25.3 of the Development Guide:

    "A generated key prevents unsafe filenames and collisions while
    preserving the original name in metadata."
    users/<user-id>/<year>/<month>/<uuid>.<ext>
"""
import hashlib
import mimetypes
import os
import uuid

from django.utils import timezone

CATEGORY_BY_EXTENSION = {
    "image": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic"},
    "video": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "audio": {".mp3", ".wav", ".ogg", ".flac", ".m4a"},
    "document": {".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"},
    "spreadsheet": {".xls", ".xlsx", ".csv", ".ods"},
    "presentation": {".ppt", ".pptx", ".odp"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz"},
}


def storage_key_upload_to(instance, filename):
    """
    upload_to callable for FileObject.file. Mirrors Section 11.1's local
    directory layout (media/users/<user-id>/...) while also matching the
    <year>/<month>/<uuid> scheme from Section 25.3, so moving to S3 later
    only means changing DEFAULT_FILE_STORAGE, not this key scheme.
    """
    ext = os.path.splitext(filename)[1].lower()
    now = timezone.now()
    owner_id = instance.owner_id or "anonymous"
    return f"users/{owner_id}/{now.year}/{now.month:02d}/{uuid.uuid4()}{ext}"


def guess_category(filename):
    ext = os.path.splitext(filename)[1].lower()
    for category, extensions in CATEGORY_BY_EXTENSION.items():
        if ext in extensions:
            return category
    return "other"


def guess_mime_type(filename):
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def compute_checksum(file_obj, chunk_size=1024 * 1024):
    """SHA-256 checksum, used for integrity checks and future duplicate detection
    (Section 10.1 "Checksum/hash"; Section 23 "Duplicate detection")."""
    hasher = hashlib.sha256()
    file_obj.seek(0)
    for chunk in iter(lambda: file_obj.read(chunk_size), b""):
        hasher.update(chunk)
    file_obj.seek(0)
    return hasher.hexdigest()
