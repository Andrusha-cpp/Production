from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from .models import Candidate, CustomUser, Bet


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("first_name", "last_name", "patronymic", "course", "group")}),
        (
            _("Permissions"),
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password1", "password2", "first_name", "last_name"),
            },
        ),
    )
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ("last_name", "first_name", "course", "group")
    search_fields = ("first_name", "last_name", "group")
    list_filter = ("course",)


@admin.register(Bet)
class BetAdmin(admin.ModelAdmin):
    list_display = ("user", "candidate", "amount", "coefficient", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__email", "candidate__last_name")
