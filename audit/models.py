from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    A lightweight, append-only record of security-relevant actions.

    Not a full activity feed -- just enough to answer "who touched this
    file/note/folder and when", which the Development Guide calls out
    under Non-Functional Requirements and Security and Privacy Design
    (Sections 5 and 15) as necessary for a system holding private data.
    """

    class Action(models.TextChoices):
        LOGIN = "login", "Logged in"
        LOGOUT = "logout", "Logged out"
        UPLOAD = "upload", "Uploaded file"
        DOWNLOAD = "download", "Downloaded file"
        PREVIEW = "preview", "Previewed file"
        RENAME = "rename", "Renamed item"
        MOVE = "move", "Moved item"
        FAVOURITE = "favourite", "Toggled favourite"
        SOFT_DELETE = "soft_delete", "Sent to recycle bin"
        RESTORE = "restore", "Restored from recycle bin"
        PERMANENT_DELETE = "permanent_delete", "Permanently deleted"
        ARCHIVE = "archive", "Archived"
        UNARCHIVE = "unarchive", "Restored from archive"
        CREATE_FOLDER = "create_folder", "Created folder"
        CREATE_NOTE = "create_note", "Created note"
        EDIT_NOTE = "edit_note", "Edited note"
        SEARCH = "search", "Performed search"
        EDIT_PROFILE = "edit_profile", "Edited profile"
        CHANGE_PASSWORD = "change_password", "Changed password"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=30, choices=Action.choices)
    object_type = models.CharField(max_length=50, blank=True)
    object_id = models.CharField(max_length=50, blank=True)
    detail = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "-created_at"]),
            models.Index(fields=["object_type", "object_id"]),
        ]

    def __str__(self):
        return f"{self.user} {self.action} {self.object_type}:{self.object_id}"
