from django import forms

from .models import Candidate


class CandidateForm(forms.ModelForm):
    class Meta:
        model = Candidate
        fields = ["first_name", "last_name", "patronymic", "course", "group", "info", "photo"]
        widgets = {
            "info": forms.Textarea(attrs={"rows": 3}),
        }
