from django.contrib import admin

from .models import FileObject


@admin.register(FileObject)
class FileObjectAdmin(admin.ModelAdmin):
    list_display = (
        "original_name",
        "owner",
        "folder",
        "category",
        "size_bytes",
        "storage_tier",
        "is_favourite",
        "is_deleted",
        "created_at",
    )
    list_filter = ("category", "storage_tier", "is_deleted", "is_favourite")
    search_fields = ("original_name", "owner__username", "tags", "checksum")
    readonly_fields = ("storage_key", "checksum", "size_bytes", "mime_type", "width", "height")
