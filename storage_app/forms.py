import os

from django import forms
from django.conf import settings

from folders.models import Folder

from .models import FileObject


def validate_uploaded_file(uploaded_file):
    """
    Enforce the guide's file-upload rules (Section 15 / OWASP File Upload
    Cheat Sheet, referenced in the guide's References section):
    validate extension and size before anything touches disk.
    """
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in settings.ALLOWED_FILE_EXTENSIONS:
        raise forms.ValidationError(f'"{uploaded_file.name}": file type "{ext}" is not allowed.')
    if uploaded_file.size > settings.MAX_UPLOAD_SIZE_BYTES:
        limit_mb = settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)
        raise forms.ValidationError(f'"{uploaded_file.name}" is larger than the {limit_mb}MB upload limit.')


# NOTE: there is deliberately no ModelForm/Form wrapping the upload input
# itself. Multi-file upload support (forms.ClearableFileInput's
# allow_multiple_selected) only landed in Django 5.0; to stay compatible
# with Django 4.2 LTS (per requirements.txt) the upload template renders
# a plain <input type="file" name="files" multiple> by hand, and the
# view reads every file with request.FILES.getlist("files") and runs
# each one through validate_uploaded_file() above.


class FileRenameForm(forms.ModelForm):
    class Meta:
        model = FileObject
        fields = ["original_name"]
        widgets = {"original_name": forms.TextInput(attrs={"class": "form-control"})}

    def clean_original_name(self):
        name = self.cleaned_data["original_name"].strip()
        if not name:
            raise forms.ValidationError("Filename cannot be empty.")
        return name


class FileTagsForm(forms.ModelForm):
    class Meta:
        model = FileObject
        fields = ["tags"]
        widgets = {"tags": forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g. receipt, 2026, tax"})}


class FileMoveForm(forms.Form):
    destination = forms.ModelChoiceField(queryset=Folder.objects.none(), required=False, label="Move to")

    def __init__(self, *args, owner=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["destination"].queryset = Folder.objects.filter(owner=owner, is_deleted=False)
        self.fields["destination"].empty_label = "My Storage (top level)"
        self.fields["destination"].widget.attrs["class"] = "form-select"
