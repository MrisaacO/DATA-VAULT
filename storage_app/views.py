from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.services import log_action
from folders.models import Folder

from .forms import FileMoveForm, FileRenameForm, FileTagsForm, validate_uploaded_file
from .models import FileObject
from .services import compute_checksum, guess_mime_type


def _owned_file_or_404(request, pk, include_deleted=False):
    qs = FileObject.objects.filter(pk=pk, owner=request.user)
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    return get_object_or_404(qs)


@login_required
def upload(request, folder_pk=None):
    folder = get_object_or_404(Folder, pk=folder_pk, owner=request.user, is_deleted=False) if folder_pk else None

    if request.method == "POST":
        uploaded_files = request.FILES.getlist("files")
        if not uploaded_files:
            messages.error(request, "Please choose at least one file.")
        else:
            created, errors = 0, []
            for uploaded_file in uploaded_files:
                try:
                    validate_uploaded_file(uploaded_file)
                except ValidationError as exc:
                    errors.append("; ".join(exc.messages))
                    continue

                file_obj = FileObject(
                    owner=request.user,
                    folder=folder,
                    file=uploaded_file,
                    original_name=uploaded_file.name,
                    mime_type=uploaded_file.content_type or guess_mime_type(uploaded_file.name),
                    size_bytes=uploaded_file.size,
                    checksum=compute_checksum(uploaded_file),
                )
                file_obj.save()
                _try_extract_image_dimensions(file_obj)
                log_action(request.user, "upload", file_obj, request=request)
                created += 1

            if created:
                messages.success(request, f"Uploaded {created} file(s).")
            for error in errors:
                messages.error(request, error)

        return redirect(folder.get_absolute_url() if folder else "dashboard:home")

    return render(
        request,
        "storage_app/upload_form.html",
        {
            "folder": folder,
            "max_upload_mb": settings.MAX_UPLOAD_SIZE_MB,
            "allowed_extensions": ", ".join(settings.ALLOWED_FILE_EXTENSIONS),
        },
    )


def _try_extract_image_dimensions(file_obj):
    if file_obj.category != "image":
        return
    try:
        from PIL import Image

        with file_obj.file.open("rb") as fh:
            with Image.open(fh) as img:
                file_obj.width, file_obj.height = img.size
        file_obj.save(update_fields=["width", "height"])
    except Exception:
        # Pillow missing, corrupt image, or unsupported format -- dimensions
        # are a nice-to-have for the UI, never a reason to fail the upload.
        pass


@login_required
def file_detail(request, pk):
    file_obj = _owned_file_or_404(request, pk)
    return render(request, "storage_app/file_detail.html", {"file_obj": file_obj})


@login_required
def file_download(request, pk):
    """
    Section 16.1: "User requests a file by application ID, not by a raw
    local path" and "If authorized, create a short-lived signed object
    URL or stream the file securely." In dev this streams straight from
    local media/; config.settings.prod swaps FileObject.file's storage
    backend for S3 without this view needing to change.
    """
    file_obj = _owned_file_or_404(request, pk)
    if file_obj.storage_tier == FileObject.StorageTier.ARCHIVED:
        messages.info(request, "This file is archived. Restore it first to download.")
        return redirect(file_obj.get_absolute_url())

    log_action(request.user, "download", file_obj, request=request)
    try:
        return FileResponse(file_obj.file.open("rb"), as_attachment=True, filename=file_obj.original_name)
    except FileNotFoundError as exc:
        raise Http404("The stored file could not be found.") from exc


@login_required
def file_preview(request, pk):
    file_obj = _owned_file_or_404(request, pk)
    if not file_obj.is_previewable:
        return redirect("storage_app:download", pk=pk)

    log_action(request.user, "preview", file_obj, request=request)
    try:
        return FileResponse(file_obj.file.open("rb"), as_attachment=False, filename=file_obj.original_name)
    except FileNotFoundError as exc:
        raise Http404("The stored file could not be found.") from exc


@login_required
def file_rename(request, pk):
    file_obj = _owned_file_or_404(request, pk)

    if request.method == "POST":
        form = FileRenameForm(request.POST, instance=file_obj)
        if form.is_valid():
            form.save()
            log_action(request.user, "rename", file_obj, request=request)
            messages.success(request, "File renamed.")
            return redirect(file_obj.get_absolute_url())
    else:
        form = FileRenameForm(instance=file_obj)

    return render(request, "storage_app/file_form.html", {"form": form, "file_obj": file_obj, "mode": "rename"})


@login_required
def file_tags(request, pk):
    file_obj = _owned_file_or_404(request, pk)

    if request.method == "POST":
        form = FileTagsForm(request.POST, instance=file_obj)
        if form.is_valid():
            form.save()
            messages.success(request, "Tags updated.")
            return redirect(file_obj.get_absolute_url())
    else:
        form = FileTagsForm(instance=file_obj)

    return render(request, "storage_app/file_form.html", {"form": form, "file_obj": file_obj, "mode": "tags"})


@login_required
def file_move(request, pk):
    file_obj = _owned_file_or_404(request, pk)

    if request.method == "POST":
        form = FileMoveForm(request.POST, owner=request.user)
        if form.is_valid():
            file_obj.folder = form.cleaned_data["destination"]
            file_obj.save(update_fields=["folder"])
            log_action(request.user, "move", file_obj, request=request)
            messages.success(request, "File moved.")
            return redirect(file_obj.get_absolute_url())
    else:
        form = FileMoveForm(owner=request.user)

    return render(request, "storage_app/file_move.html", {"form": form, "file_obj": file_obj})


@login_required
def file_toggle_favourite(request, pk):
    file_obj = _owned_file_or_404(request, pk)
    if request.method == "POST":
        file_obj.is_favourite = not file_obj.is_favourite
        file_obj.save(update_fields=["is_favourite"])
        log_action(request.user, "favourite", file_obj, request=request)
    return redirect(request.META.get("HTTP_REFERER") or file_obj.get_absolute_url())


@login_required
def favourites(request):
    files = FileObject.objects.filter(owner=request.user, is_deleted=False, is_favourite=True)
    return render(request, "storage_app/favourites.html", {"files": files})


@login_required
def file_delete(request, pk):
    """Soft-delete into the recycle bin (Section 14.1)."""
    file_obj = _owned_file_or_404(request, pk)

    if request.method == "POST":
        file_obj.is_deleted = True
        file_obj.deleted_at = timezone.now()
        file_obj.save(update_fields=["is_deleted", "deleted_at"])
        log_action(request.user, "soft_delete", file_obj, request=request)
        messages.success(request, f'"{file_obj.original_name}" moved to the recycle bin.')
        return redirect(file_obj.folder.get_absolute_url() if file_obj.folder else "dashboard:home")

    return render(request, "storage_app/file_confirm_delete.html", {"file_obj": file_obj})


@login_required
def recycle_bin(request):
    from folders.models import Folder
    from notes.models import Note

    files = FileObject.objects.filter(owner=request.user, is_deleted=True)
    folders = Folder.objects.filter(owner=request.user, is_deleted=True)
    notes = Note.objects.filter(owner=request.user, is_deleted=True)
    return render(
        request,
        "storage_app/recycle_bin.html",
        {"files": files, "folders": folders, "notes": notes, "retention_days": _retention_days()},
    )


def _retention_days():
    from django.conf import settings

    return settings.RECYCLE_BIN_RETENTION_DAYS


@login_required
def file_restore(request, pk):
    file_obj = _owned_file_or_404(request, pk, include_deleted=True)
    file_obj.is_deleted = False
    file_obj.deleted_at = None
    file_obj.save(update_fields=["is_deleted", "deleted_at"])
    log_action(request.user, "restore", file_obj, request=request)
    messages.success(request, f'"{file_obj.original_name}" restored.')
    return redirect("storage_app:recycle_bin")


@login_required
def file_permanent_delete(request, pk):
    file_obj = _owned_file_or_404(request, pk, include_deleted=True)

    if request.method == "POST":
        name = file_obj.original_name
        log_action(request.user, "permanent_delete", file_obj, detail=name, request=request)
        file_obj.file.delete(save=False)
        file_obj.delete()
        messages.success(request, f'"{name}" permanently deleted.')
        return redirect("storage_app:recycle_bin")

    return render(request, "storage_app/file_confirm_permanent_delete.html", {"file_obj": file_obj})
