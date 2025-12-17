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
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "patronymic": "Отчество",
            "course": "Курс",
            "group": "Группа",
            "info": "Описание",
            "photo": "Фото",
        }
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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name", "patronymic", "course", "group"]
        labels = {
            "first_name": "Имя",
            "last_name": "Фамилия",
            "patronymic": "Отчество",
            "course": "Курс",
            "group": "Группа",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            existing_classes = field.widget.attrs.get("class", "")
            field.widget.attrs["class"] = (existing_classes + " form-control").strip()


class AdminUserForm(forms.ModelForm):
    password = forms.CharField(label="Пароль", required=False, widget=forms.PasswordInput())

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name", "patronymic", "course", "group", "is_staff", "is_active"]
        labels = {
            "email": "Почта",
            "first_name": "Имя",
            "last_name": "Фамилия",
            "patronymic": "Отчество",
            "course": "Курс",
            "group": "Группа",
            "is_staff": "Админ",
            "is_active": "Активен",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            existing_classes = field.widget.attrs.get("class", "")
            if field.widget.__class__.__name__ == "CheckboxInput":
                field.widget.attrs["class"] = (existing_classes + " form-check-input").strip()
            else:
                field.widget.attrs["class"] = (existing_classes + " form-control").strip()

    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").lower()
        qs = CustomUser.objects.filter(email=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("Пользователь с таким email уже существует.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        user.username = user.email
        if password:
            user.set_password(password)
        if commit:
            user.save()
        return user
