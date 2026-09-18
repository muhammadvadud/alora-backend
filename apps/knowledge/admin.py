from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import ChoicesDropdownFilter, ChoicesRadioFilter
from unfold.decorators import display

from .models import KnowledgeRule


@admin.register(KnowledgeRule)
class KnowledgeRuleAdmin(ModelAdmin):
    list_display = ("kind_badge", "priority", "recommendation", "is_active", "created_at")
    list_filter = (
        ("kind", ChoicesDropdownFilter),
        ("is_active", ChoicesRadioFilter),
    )
    search_fields = ("recommendation", "kind")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (
            _("Qoida"),
            {"fields": ("kind", "priority", "condition", "recommendation")},
        ),
        (_("Faollik"), {"fields": ("is_active",)}),
        (_("Tizim maydonlari"), {"fields": ("created_at", "updated_at")}),
    )

    @display(
        description=_("Turi"),
        label={
            KnowledgeRule.Kind.ROOM_STYLE: "primary",
            KnowledgeRule.Kind.LIGHT: "warning",
            KnowledgeRule.Kind.COLOR: "info",
            KnowledgeRule.Kind.CONSTRUCTION: "danger",
            KnowledgeRule.Kind.OBJECTION: "warning",
            KnowledgeRule.Kind.GENERAL: "default",
        },
    )
    def kind_badge(self, obj: KnowledgeRule) -> tuple[str, str]:
        return obj.kind, obj.get_kind_display()
