from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.services import log_action

from .forms import FolderForm, FolderMoveForm
from .models import Folder


def _owned_folder_or_404(request, pk, include_deleted=False):
    # Ownership rule from Section 25.2 of the guide: never look a private
    # object up by ID alone -- always scope the query to request.user.
    qs = Folder.objects.filter(pk=pk, owner=request.user)
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    return get_object_or_404(qs)


@login_required
def folder_detail(request, pk=None):
    from notes.models import Note
    from storage_app.models import FileObject

    folder = _owned_folder_or_404(request, pk) if pk else None

    subfolders = Folder.objects.filter(owner=request.user, parent=folder, is_deleted=False)
    files = FileObject.objects.filter(owner=request.user, folder=folder, is_deleted=False)
    notes = Note.objects.filter(owner=request.user, folder=folder, is_deleted=False)

    query = request.GET.get("sort", "name")
    sort_map = {
        "name": "original_name",
        "-name": "-original_name",
        "date": "created_at",
        "-date": "-created_at",
        "size": "size_bytes",
        "-size": "-size_bytes",
    }
    files = files.order_by(sort_map.get(query, "original_name"))

    breadcrumbs = folder.get_ancestors() + [folder] if folder else []

    return render(
        request,
        "folders/folder_detail.html",
        {
            "folder": folder,
            "subfolders": subfolders,
            "files": files,
            "notes": notes,
            "breadcrumbs": breadcrumbs,
            "current_sort": query,
        },
    )


@login_required
def folder_create(request, pk=None):
    parent = _owned_folder_or_404(request, pk) if pk else None

    if request.method == "POST":
        form = FolderForm(request.POST, owner=request.user, parent=parent)
        if form.is_valid():
            folder = form.save()
            log_action(request.user, "create_folder", folder, request=request)
            messages.success(request, f'Folder "{folder.name}" created.')
            return redirect(folder.get_absolute_url() if parent else "dashboard:home")
    else:
        form = FolderForm(owner=request.user, parent=parent)

    return render(request, "folders/folder_form.html", {"form": form, "parent": parent, "mode": "create"})


@login_required
def folder_rename(request, pk):
    folder = _owned_folder_or_404(request, pk)

    if request.method == "POST":
        form = FolderForm(request.POST, owner=request.user, parent=folder.parent, instance=folder)
        if form.is_valid():
            form.save()
            log_action(request.user, "rename", folder, request=request)
            messages.success(request, "Folder renamed.")
            return redirect(folder.get_absolute_url())
    else:
        form = FolderForm(owner=request.user, parent=folder.parent, instance=folder)

    return render(request, "folders/folder_form.html", {"form": form, "folder": folder, "mode": "rename"})


@login_required
def folder_move(request, pk):
    folder = _owned_folder_or_404(request, pk)

    if request.method == "POST":
        form = FolderMoveForm(request.POST, owner=request.user, instance=folder)
        if form.is_valid():
            new_parent = form.cleaned_data["destination"]
            name_taken = (
                Folder.objects.filter(owner=request.user, parent=new_parent, name=folder.name, is_deleted=False)
                .exclude(pk=folder.pk)
                .exists()
            )
            if name_taken:
                form.add_error(None, "A folder with this name already exists at the destination.")
            else:
                folder.parent = new_parent
                try:
                    # Re-checks the self-ancestry cycle guard directly
                    # (not full_clean(), which would also re-run the
                    # (owner, parent, name) UniqueConstraint check we
                    # already did above as name_taken). FolderMoveForm's
                    # queryset already excludes folder and its own
                    # descendants from the choices, so this shouldn't
                    # trigger in practice -- it's a defense-in-depth
                    # check against a tampered POST body, caught here so
                    # it can't 500.
                    folder.clean()
                except ValidationError as exc:
                    form.add_error(None, exc)
                else:
                    folder.save()
                    log_action(request.user, "move", folder, request=request)
                    messages.success(request, "Folder moved.")
                    return redirect(folder.get_absolute_url())
    else:
        form = FolderMoveForm(owner=request.user, instance=folder)

    return render(request, "folders/folder_move.html", {"form": form, "folder": folder})


@login_required
def folder_delete(request, pk):
    """Soft-delete: the folder goes to the recycle bin, matching Section 14.1."""
    folder = _owned_folder_or_404(request, pk)

    if request.method == "POST":
        folder.is_deleted = True
        folder.deleted_at = timezone.now()
        folder.save(update_fields=["is_deleted", "deleted_at"])
        log_action(request.user, "soft_delete", folder, request=request)
        messages.success(request, f'"{folder.name}" moved to the recycle bin.')
        return redirect(folder.parent.get_absolute_url() if folder.parent else "dashboard:home")

    return render(request, "folders/folder_confirm_delete.html", {"folder": folder})


@login_required
def folder_restore(request, pk):
    folder = _owned_folder_or_404(request, pk, include_deleted=True)
    folder.is_deleted = False
    folder.deleted_at = None
    folder.save(update_fields=["is_deleted", "deleted_at"])
    log_action(request.user, "restore", folder, request=request)
    messages.success(request, f'"{folder.name}" restored.')
    return redirect("storage_app:recycle_bin")


@login_required
def folder_permanent_delete(request, pk):
    folder = _owned_folder_or_404(request, pk, include_deleted=True)

    if request.method == "POST":
        name = folder.name
        log_action(request.user, "permanent_delete", folder, detail=name, request=request)
        folder.delete()
        messages.success(request, f'"{name}" permanently deleted.')
        return redirect("storage_app:recycle_bin")

    return render(request, "folders/folder_confirm_permanent_delete.html", {"folder": folder})
