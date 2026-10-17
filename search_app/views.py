from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from audit.services import log_action
from notes.models import Note
from storage_app.models import FileObject


@login_required
def search(request):
    """
    "Search by filename, note text, tags, file type and date" (Section
    4). Kept as simple `icontains`/date-range filtering for Version 1;
    Section 23's "full-text document search" / OCR is a later enhancement.
    """
    query = request.GET.get("q", "").strip()
    file_type = request.GET.get("type", "")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")

    files = FileObject.objects.none()
    notes = Note.objects.none()

    if query or file_type or date_from or date_to:
        files = FileObject.objects.filter(owner=request.user, is_deleted=False)
        notes = Note.objects.filter(owner=request.user, is_deleted=False)

        if query:
            files = files.filter(Q(original_name__icontains=query) | Q(tags__icontains=query))
            notes = notes.filter(Q(title__icontains=query) | Q(content__icontains=query))

        if file_type:
            files = files.filter(category=file_type)
            notes = notes.none()  # a file-type filter doesn't apply to notes

        if date_from:
            files = files.filter(created_at__date__gte=date_from)
            notes = notes.filter(created_at__date__gte=date_from)

        if date_to:
            files = files.filter(created_at__date__lte=date_to)
            notes = notes.filter(created_at__date__lte=date_to)

        if query:
            log_action(request.user, "search", detail=query, request=request)

    return render(
        request,
        "search_app/results.html",
        {
            "query": query,
            "file_type": file_type,
            "date_from": date_from,
            "date_to": date_to,
            "files": files,
            "notes": notes,
            "has_search": bool(query or file_type or date_from or date_to),
        },
    )
