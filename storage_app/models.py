from django.conf import settings
from django.db import models
from django.urls import reverse

from .services import guess_category, storage_key_upload_to


class FileObject(models.Model):
    """
    Metadata + binary content for one uploaded file.

    Field set follows the "Simplified file metadata model" in Section
    25.1 of the Development Guide, extended with the bits Version 1
    actually needs to serve files (the FileField itself, timestamps for
    the recycle bin and archive workflow).
    """

    class StorageTier(models.TextChoices):
        ACTIVE = "active", "Active"
        ARCHIVED = "archived", "Archived"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="files")
    folder = models.ForeignKey(
        "folders.Folder",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="files",
    )

    file = models.FileField(upload_to=storage_key_upload_to, max_length=700)
    original_name = models.CharField(max_length=255)
    # null=True (not blank/empty-string) so that the very first INSERT --
    # before Django's FileField.pre_save has actually committed the file
    # to storage and picked its final generated name -- can happen
    # without violating uniqueness: NULL is exempt from unique
    # constraints, but two rows both holding '' would collide on the
    # second upload. save() below fills this in immediately afterwards.
    storage_key = models.CharField(max_length=700, unique=True, null=True, blank=True)
    mime_type = models.CharField(max_length=150)
    category = models.CharField(max_length=30, blank=True)
    size_bytes = models.BigIntegerField(default=0)
    checksum = models.CharField(max_length=128, blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma-separated tags")

    is_favourite = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    storage_tier = models.CharField(max_length=30, choices=StorageTier.choices, default=StorageTier.ACTIVE)
    archived_at = models.DateTimeField(null=True, blank=True)

    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["original_name"]
        indexes = [
            models.Index(fields=["owner", "is_deleted"]),
            models.Index(fields=["owner", "folder"]),
            models.Index(fields=["owner", "storage_tier"]),
            models.Index(fields=["owner", "is_favourite"]),
        ]

    def __str__(self):
        return self.original_name

    def save(self, *args, **kwargs):
        if not self.category:
            self.category = guess_category(self.original_name)

        # Let Django's FileField.pre_save actually commit the file to
        # storage first (via upload_to) -- only after that does
        # self.file.name hold the real, final generated path. Setting
        # storage_key from self.file.name *before* this super().save()
        # call would capture the original uploaded filename instead
        # (see the comment on the field above).
        super().save(*args, **kwargs)

        if self.file and self.storage_key != self.file.name:
            self.storage_key = self.file.name
            super().save(update_fields=["storage_key"])

    def get_absolute_url(self):
        return reverse("storage_app:detail", args=[self.pk])

    @property
    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    @property
    def extension(self):
        return self.original_name.rsplit(".", 1)[-1].lower() if "." in self.original_name else ""

    @property
    def is_previewable(self):
        return self.category in {"image", "audio", "video"} or self.mime_type == "application/pdf"
