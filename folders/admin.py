from django.contrib import admin

from .models import Folder


@admin.register(Folder)
class FolderAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "parent", "is_deleted", "created_at")
    list_filter = ("is_deleted",)
    search_fields = ("name", "owner__username")
