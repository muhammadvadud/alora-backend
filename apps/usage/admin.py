from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RangeDateFilter,
    RangeDateTimeFilter,
)
from unfold.decorators import display

from apps.common.choices import OnExceed

from .models import UsageDaily, UsageLimit, UsageRecord


def _fmt_uzs(value) -> str:
    return f"{value:,.2f} UZS" if value is not None else "—"


@admin.register(UsageRecord)
class UsageRecordAdmin(ModelAdmin):
    list_display = (
        "user",
        "provider",
        "model",
        "prompt_tokens",
        "completion_tokens",
        "cost_uzs_display",
    )
    list_filter = (
        ("provider", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
        ("user", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("user__phone", "model", "provider")
    readonly_fields = ("created_at", "updated_at", "cost_uzs_display", "cost_usd_display")
    fieldsets = (
        (
            _("Foydalanuvchi"),
            {"fields": ("user", "conversation", "message_id")},
        ),
        (
            _("Model"),
            {"fields": ("provider", "model")},
        ),
        (
            _("Tokenlar"),
            {
                "fields": (
                    "prompt_tokens",
                    "completion_tokens",
                    "cached_tokens",
                    "reasoning_tokens",
                )
            },
        ),
        (
            _("Ovoz va asboblar"),
            {"fields": ("stt_seconds", "tts_chars", "tool_calls", "latency_ms")},
        ),
        (
            _("Xarajat"),
            {"fields": ("cost_usd", "cost_usd_display", "cost_uzs", "cost_uzs_display")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Xarajat (UZS)"))
    def cost_uzs_display(self, obj: UsageRecord) -> str:
        return _fmt_uzs(obj.cost_uzs)

    @display(description=_("Xarajat (USD)"))
    def cost_usd_display(self, obj: UsageRecord) -> str:
        return f"${obj.cost_usd:,.4f}" if obj.cost_usd is not None else "—"


@admin.register(UsageDaily)
class UsageDailyAdmin(ModelAdmin):
    list_display = (
        "date",
        "user",
        "tokens",
        "messages_count",
        "conversations_count",
        "cost_uzs_display",
    )
    list_filter = (
        ("date", RangeDateFilter),
        ("user", admin.RelatedOnlyFieldListFilter),
    )
    search_fields = ("user__phone",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Yig'ma"),
            {
                "fields": (
                    "date",
                    "user",
                    "tokens",
                    "cost_uzs",
                    "messages_count",
                    "conversations_count",
                )
            },
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Xarajat (UZS)"))
    def cost_uzs_display(self, obj: UsageDaily) -> str:
        return _fmt_uzs(obj.cost_uzs)


@admin.register(UsageLimit)
class UsageLimitAdmin(ModelAdmin):
    list_display = (
        "user",
        "role_badge",
        "period",
        "max_tokens",
        "max_cost_display",
        "on_exceed_badge",
        "is_active",
    )
    list_filter = (
        ("role", ChoicesDropdownFilter),
        ("period", ChoicesDropdownFilter),
        ("on_exceed", ChoicesDropdownFilter),
        ("is_active", BooleanRadioFilter),
    )
    search_fields = ("user__phone",)
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Qamrov"),
            {"fields": ("user", "role", "period")},
        ),
        (
            _("Limitlar"),
            {"fields": ("is_unlimited", "max_tokens", "max_cost_uzs", "max_messages")},
        ),
        (
            _("Xatti-harakat"),
            {"fields": ("on_exceed",)},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(
        description=_("Rol"),
        label={"any": "default", "employee": "info", "manager": "warning", "admin": "success"},
    )
    def role_badge(self, obj: UsageLimit) -> tuple[str, str]:
        role = obj.role if obj.role else "any"
        return role, obj.get_role_display() if obj.role else _("Har qanday")

    @display(description=_("Maksimal xarajat (UZS)"))
    def max_cost_display(self, obj: UsageLimit) -> str:
        if obj.is_unlimited:
            return _("Cheksiz")
        return _fmt_uzs(obj.max_cost_uzs)

    @display(
        description=_("Oshganda"),
        label={OnExceed.WARN: "warning", OnExceed.BLOCK: "danger"},
    )
    def on_exceed_badge(self, obj: UsageLimit) -> tuple[str, str]:
        return obj.on_exceed, obj.get_on_exceed_display()
