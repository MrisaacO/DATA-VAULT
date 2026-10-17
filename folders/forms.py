from django import forms

from .models import Folder


class FolderForm(forms.ModelForm):
    class Meta:
        model = Folder
        fields = ["name"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "autofocus": True, "placeholder": "Folder name"}),
        }

    def __init__(self, *args, owner=None, parent=None, **kwargs):
        self.owner = owner
        self.parent = parent
        super().__init__(*args, **kwargs)

    def clean_name(self):
        name = self.cleaned_data["name"].strip()
        if not name:
            raise forms.ValidationError("Folder name cannot be empty.")
        if "/" in name or "\\" in name:
            raise forms.ValidationError("Folder name cannot contain slashes.")

        # Checked here (rather than left to Folder.full_clean() /
        # validate_unique() inside save()) so a collision comes back as a
        # normal form error instead of an uncaught ValidationError -- and
        # so it's caught even when parent is None, where the database's
        # own unique constraint can't help (NULL isn't unique-constrained
        # the same way across most backends, including SQLite/Postgres).
        siblings = Folder.objects.filter(owner=self.owner, parent=self.parent, name=name, is_deleted=False)
        if self.instance.pk:
            siblings = siblings.exclude(pk=self.instance.pk)
        if siblings.exists():
            raise forms.ValidationError("A folder with this name already exists here.")

        return name

    def save(self, commit=True):
        folder = super().save(commit=False)
        folder.owner = self.owner
        folder.parent = self.parent
        if commit:
            folder.save()
        return folder


class FolderMoveForm(forms.Form):
    destination = forms.ModelChoiceField(queryset=Folder.objects.none(), required=False, label="Move to")

    def __init__(self, *args, owner=None, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance = instance
        excluded_ids = {instance.pk}
        node_stack = list(instance.children.all())
        while node_stack:
            node = node_stack.pop()
            excluded_ids.add(node.pk)
            node_stack.extend(node.children.all())
        self.fields["destination"].queryset = Folder.objects.filter(owner=owner, is_deleted=False).exclude(
            pk__in=excluded_ids
        )
        self.fields["destination"].empty_label = "My Storage (top level)"
        self.fields["destination"].widget.attrs["class"] = "form-select"
