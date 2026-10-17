from django.contrib import admin

from .models import Note


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "folder", "is_favourite", "is_pinned", "is_deleted", "updated_at")
    list_filter = ("is_deleted", "is_favourite", "is_pinned")
    search_fields = ("title", "content", "owner__username")
