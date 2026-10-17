from django import forms

from .models import Note


class NoteForm(forms.ModelForm):
    class Meta:
        model = Note
        fields = ["title", "content", "is_pinned"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control", "placeholder": "Note title"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 14}),
            "is_pinned": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean_title(self):
        title = self.cleaned_data["title"].strip()
        if not title:
            raise forms.ValidationError("Please give the note a title.")
        return title
