from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    BooleanRadioFilter,
    ChoicesDropdownFilter,
    RangeDateTimeFilter,
)
from unfold.decorators import display

from .models import Conversation, ConversationStatus, Message


class MessageInline(TabularInline):
    model = Message
    extra = 0
    classes = ["collapse"]
    readonly_fields = ("created_at", "updated_at")
    fields = ("role", "content", "tokens_in", "tokens_out", "audio_url", "created_at")


@admin.register(Conversation)
class ConversationAdmin(ModelAdmin):
    ordering = ("-created_at",)

    list_display = ("title", "user", "status_badge", "mode", "stage_badge", "created_at")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("mode", ChoicesDropdownFilter),
        ("stage", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("title", "session_id")
    readonly_fields = ("created_at", "updated_at", "started_at", "last_message_at")
    inlines = [MessageInline]
    fieldsets = (
        (
            _("Suhbat"),
            {"fields": ("title", "session_id", "user", "order")},
        ),
        (
            _("Holat"),
            {"fields": ("status", "mode", "stage", "context")},
        ),
        (
            _("Vaqt"),
            {"fields": ("started_at", "last_message_at")},
        ),
        (_("Tenant va faollik"), {"fields": ("tenant", "is_active")}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(
        description=_("Holat"),
        label={ConversationStatus.ACTIVE: "success", ConversationStatus.ARCHIVED: "info"},
    )
    def status_badge(self, obj: Conversation) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(
        description=_("Bosqich"),
        label={
            "need": "info",
            "recommend": "primary",
            "measure": "warning",
            "calc": "warning",
            "variants": "primary",
            "order": "success",
        },
    )
    def stage_badge(self, obj: Conversation) -> tuple[str, str]:
        return obj.stage, obj.get_stage_display()


@admin.register(Message)
class MessageAdmin(ModelAdmin):
    ordering = ("-created_at",)

    list_display = ("conversation", "role_badge", "tokens_in", "tokens_out", "created_at")
    list_filter = (
        ("role", ChoicesDropdownFilter),
        ("is_active", BooleanRadioFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("content", "conversation__title", "conversation__session_id")
    readonly_fields = ("id", "created_at", "updated_at")
    fieldsets = (
        (
            _("Xabar"),
            {"fields": ("conversation", "role", "content")},
        ),
        (
            _("Tokenlar"),
            {"fields": ("tokens_in", "tokens_out")},
        ),
        (
            _("Asboblar va media"),
            {"fields": ("tool_calls", "tool_result", "audio_url")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("id", "created_at", "updated_at")}),
    )

    @display(
        description=_("Rol"),
        label={
            "user": "primary",
            "assistant": "success",
            "tool": "warning",
            "system": "info",
        },
    )
    def role_badge(self, obj: Message) -> tuple[str, str]:
        return obj.role, obj.get_role_display()
