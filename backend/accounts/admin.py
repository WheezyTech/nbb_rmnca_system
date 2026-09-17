from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "facility",
        "phone",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    list_filter = (
        "role",
        "facility",
        "is_active",
        "is_staff",
        "is_superuser",
    )

    search_fields = (
        "username",
        "email",
        "first_name",
        "last_name",
        "phone",
    )

    ordering = ("username",)

    fieldsets = UserAdmin.fieldsets + (
        (
            "National Blood Bank System Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "facility",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "National Blood Bank System Information",
            {
                "fields": (
                    "role",
                    "phone",
                    "facility",
                )
            },
        ),
    )