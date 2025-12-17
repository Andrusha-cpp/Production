from django import forms

from .models import Candidate, CustomUser


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


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput(attrs={"class": "form-control"}))
    password_confirm = forms.CharField(
        label="Повторите пароль",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "email", "course", "group"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "email": "Email",
            "course": "Курс",
            "group": "Группа",
        }

    def clean(self):
        cleaned = super().clean()
        pwd = cleaned.get("password")
        pwd2 = cleaned.get("password_confirm")
        if pwd and pwd2 and pwd != pwd2:
            self.add_error("password_confirm", "Пароли не совпадают.")
        return cleaned
