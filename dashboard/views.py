from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.shortcuts import render

from folders.models import Folder
from notes.models import Note
from storage_app.models import FileObject
from storage_app.services import CATEGORY_BY_EXTENSION


@login_required
def home(request):
    """
    The "simple personal drive" landing page described in Section 17:
    top-level folders, recent files, quick storage-by-category, matching
    the example dashboard layout in Section 17.1.
    """
    user = request.user

    top_level_folders = Folder.objects.filter(owner=user, parent=None, is_deleted=False)
    top_level_files = FileObject.objects.filter(owner=user, folder=None, is_deleted=False)
    top_level_notes = Note.objects.filter(owner=user, folder=None, is_deleted=False)

    recent_files = FileObject.objects.filter(owner=user, is_deleted=False).order_by("-created_at")[:8]

    by_category = (
        FileObject.objects.filter(owner=user, is_deleted=False)
        .values("category")
        .annotate(total_bytes=Sum("size_bytes"), count=Count("id"))
        .order_by("-total_bytes")
    )

    return render(
        request,
        "dashboard/home.html",
        {
            "folders": top_level_folders,
            "files": top_level_files,
            "notes": top_level_notes,
            "recent_files": recent_files,
            "by_category": by_category,
            "categories": sorted(CATEGORY_BY_EXTENSION.keys()) + ["other"],
        },
    )
