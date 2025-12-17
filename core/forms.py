from django import forms

from .models import Candidate


class CandidateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()

    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "patronymic", "course", "group", "info", "photo"]
        widgets = {
            "info": forms.Textarea(attrs={"rows": 3}),
        }
