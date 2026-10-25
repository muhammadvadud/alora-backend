from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter, ChoicesRadioFilter
from unfold.decorators import display

from .models import PromptVersion


@admin.register(PromptVersion)
class PromptVersionAdmin(ModelAdmin):
    list_display = ("version", "author", "current_badge", "content_preview", "created_at")
    list_filter = (
        ("is_current", ChoicesRadioFilter),
        ("is_active", BooleanRadioFilter),
    )
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at", "content_preview")
    fieldsets = (
        (
            _("Versiya"),
            {"fields": ("version", "author", "content", "content_preview", "is_current")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Joriy"), label={True: "success", False: "default"})
    def current_badge(self, obj: PromptVersion) -> tuple[bool, str]:
        if obj.is_current:
            return True, str(_("Joriy"))
        return False, str(_("Arxiv"))

    @display(description=_("Matn"), ordering="version")
    def content_preview(self, obj: PromptVersion) -> str:
        text = obj.content.replace("\n", " ")
        return text[:80] + ("…" if len(text) > 80 else "")
