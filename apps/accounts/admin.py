from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesRadioFilter, RangeDateTimeFilter
from unfold.decorators import display

from apps.common.choices import UserRole

from .models import Tenant, User


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


@admin.register(Tenant)
class TenantAdmin(ModelAdmin):
    list_display = ("name", "phone", "currency", "is_active", "created_at")
    list_filter = (
        ("is_active", ChoicesRadioFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("name", "phone")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Asosiy ma'lumotlar"),
            {"fields": ("name", "phone", "address", "currency", "timezone")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = (
        "phone",
        "full_name",
        "role_badge",
        "tenant",
        "is_staff",
        "is_active",
        "created_at",
    )
    list_filter = (
        ("role", ChoicesRadioFilter),
        ("is_active", ChoicesRadioFilter),
        ("tenant", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("phone", "full_name")
    readonly_fields = ("created_at", "updated_at", "password_state")
    fieldsets = (
        (
            _("Foydalanuvchi ma'lumotlari"),
            {"fields": ("phone", "full_name", "role", "tenant")},
        ),
        (
            _("Xavfsizlik va kirish"),
            {"fields": ("password_state", "is_staff", "device_id")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description="Parol", label={"has": "success", "none": "default"})
    def password_state(self, obj: User) -> tuple[str, str]:
        if obj.has_usable_password():
            return "has", _("O'rnatilgan")
        return "none", _("O'rnatilmagan")

    @display(
        description=_("Rol"),
        label={
            UserRole.EMPLOYEE: "info",
            UserRole.MANAGER: "warning",
            UserRole.ADMIN: "success",
        },
    )
    def role_badge(self, obj: User) -> tuple[str, str]:
        return obj.role, obj.get_role_display()
