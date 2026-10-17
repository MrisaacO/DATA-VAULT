from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from audit.services import log_action
from folders.models import Folder

from .forms import NoteForm
from .models import Note


def _owned_note_or_404(request, pk, include_deleted=False):
    qs = Note.objects.filter(pk=pk, owner=request.user)
    if not include_deleted:
        qs = qs.filter(is_deleted=False)
    return get_object_or_404(qs)


@login_required
def note_list(request):
    notes = Note.objects.filter(owner=request.user, is_deleted=False)
    return render(request, "notes/note_list.html", {"notes": notes})


@login_required
def note_detail(request, pk):
    note = _owned_note_or_404(request, pk)
    return render(request, "notes/note_detail.html", {"note": note})


@login_required
def note_create(request, folder_pk=None):
    folder = get_object_or_404(Folder, pk=folder_pk, owner=request.user, is_deleted=False) if folder_pk else None

    if request.method == "POST":
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.owner = request.user
            note.folder = folder
            note.save()
            log_action(request.user, "create_note", note, request=request)
            messages.success(request, "Note created.")
            return redirect(note.get_absolute_url())
    else:
        form = NoteForm()

    return render(request, "notes/note_form.html", {"form": form, "folder": folder, "mode": "create"})


@login_required
def note_edit(request, pk):
    note = _owned_note_or_404(request, pk)

    if request.method == "POST":
        form = NoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            log_action(request.user, "edit_note", note, request=request)
            messages.success(request, "Note saved.")
            return redirect(note.get_absolute_url())
    else:
        form = NoteForm(instance=note)

    return render(request, "notes/note_form.html", {"form": form, "note": note, "folder": note.folder, "mode": "edit"})


@login_required
def note_toggle_favourite(request, pk):
    note = _owned_note_or_404(request, pk)
    if request.method == "POST":
        note.is_favourite = not note.is_favourite
        note.save(update_fields=["is_favourite"])
        log_action(request.user, "favourite", note, request=request)
    return redirect(request.META.get("HTTP_REFERER") or note.get_absolute_url())


@login_required
def note_delete(request, pk):
    note = _owned_note_or_404(request, pk)

    if request.method == "POST":
        note.is_deleted = True
        note.deleted_at = timezone.now()
        note.save(update_fields=["is_deleted", "deleted_at"])
        log_action(request.user, "soft_delete", note, request=request)
        messages.success(request, f'"{note.title}" moved to the recycle bin.')
        return redirect(note.folder.get_absolute_url() if note.folder else "dashboard:home")

    return render(request, "notes/note_confirm_delete.html", {"note": note})


@login_required
def note_restore(request, pk):
    note = _owned_note_or_404(request, pk, include_deleted=True)
    note.is_deleted = False
    note.deleted_at = None
    note.save(update_fields=["is_deleted", "deleted_at"])
    log_action(request.user, "restore", note, request=request)
    messages.success(request, f'"{note.title}" restored.')
    return redirect("storage_app:recycle_bin")


@login_required
def note_permanent_delete(request, pk):
    note = _owned_note_or_404(request, pk, include_deleted=True)

    if request.method == "POST":
        title = note.title
        log_action(request.user, "permanent_delete", note, detail=title, request=request)
        note.delete()
        messages.success(request, f'"{title}" permanently deleted.')
        return redirect("storage_app:recycle_bin")

    return render(request, "notes/note_confirm_permanent_delete.html", {"note": note})
