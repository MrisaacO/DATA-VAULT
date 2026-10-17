from django.conf import settings
from django.db import models
from django.urls import reverse


class Note(models.Model):
    """
    Notes are stored as database content rather than binary files, per the
    Executive Summary of the Development Guide: "Notes are stored as
    database content, while large binary files are stored in a file
    system ... or private object storage."
    """

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes")
    folder = models.ForeignKey(
        "folders.Folder",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    is_favourite = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-updated_at"]
        indexes = [
            models.Index(fields=["owner", "is_deleted"]),
            models.Index(fields=["owner", "folder"]),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("notes:detail", args=[self.pk])
