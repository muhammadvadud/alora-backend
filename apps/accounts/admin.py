from django.contrib import admin
from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesRadioFilter, RangeDateTimeFilter
from unfold.decorators import display

from apps.common.choices import UserRole

from .models import Tenant, User


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


class UserAdminForm(forms.ModelForm):
    """Admin orqali parolni xavfsiz yangilash formasi.

    Amaldagi parol hech qachon ko'rsatilmaydi. Maydonlar bo'sh qolsa,
    foydalanuvchining hozirgi paroli o'zgarmaydi.
    """

    password = forms.CharField(
        label=_("Yangi parol"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
        help_text=_("O'zgartirmasangiz bo'sh qoldiring."),
    )
    password_confirmation = forms.CharField(
        label=_("Yangi parolni takrorlang"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False),
    )

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_password = self.instance.password

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmation = cleaned_data.get("password_confirmation")
        if not password and not confirmation:
            return cleaned_data
        if not password or password != confirmation:
            raise ValidationError(_("Yangi parollar bir xil bo'lishi kerak."))
        password_validation.validate_password(password, self.instance)
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")
        if password:
            user.set_password(password)
        else:
            user.password = self._original_password
        if commit:
            user.save()
            self.save_m2m()
        return user


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
    form = UserAdminForm
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
            {
                "fields": (
                    "password_state",
                    "password",
                    "password_confirmation",
                    "is_staff",
                    "device_id",
                )
            },
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
