from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.services import log_action
from storage_app.models import FileObject

"""
Section 13.2's "Manual archive feature" describes a background job that
moves the object into a cheaper storage tier after the user requests it.
Version 1 has no background workers yet (Celery/Redis are listed as a
"later" addition in the recommended stack), so archiving here just flips
storage_tier synchronously. The status field and view boundary are kept
identical to what a real async job would set, so wiring in Celery later
is a matter of dispatching a task from archive_file() instead of doing
the update inline -- not a data model change.
"""


@login_required
def archive_list(request):
    files = FileObject.objects.filter(owner=request.user, is_deleted=False, storage_tier=FileObject.StorageTier.ARCHIVED)
    return render(request, "archive_app/archive_list.html", {"files": files})


@login_required
def archive_file(request, pk):
    file_obj = get_object_or_404(FileObject, pk=pk, owner=request.user, is_deleted=False)

    if request.method == "POST":
        file_obj.storage_tier = FileObject.StorageTier.ARCHIVED
        file_obj.archived_at = timezone.now()
        file_obj.save(update_fields=["storage_tier", "archived_at"])
        log_action(request.user, "archive", file_obj, request=request)
        messages.success(request, f'"{file_obj.original_name}" archived.')
        return redirect(file_obj.folder.get_absolute_url() if file_obj.folder else "dashboard:home")

    return render(request, "archive_app/archive_confirm.html", {"file_obj": file_obj, "action": "archive"})


@login_required
def unarchive_file(request, pk):
    file_obj = get_object_or_404(FileObject, pk=pk, owner=request.user, is_deleted=False)

    if request.method == "POST":
        file_obj.storage_tier = FileObject.StorageTier.ACTIVE
        file_obj.archived_at = None
        file_obj.save(update_fields=["storage_tier", "archived_at"])
        log_action(request.user, "unarchive", file_obj, request=request)
        messages.success(request, f'"{file_obj.original_name}" restored from the archive.')
        return redirect("archive_app:archive_list")

    return render(request, "archive_app/archive_confirm.html", {"file_obj": file_obj, "action": "unarchive"})
