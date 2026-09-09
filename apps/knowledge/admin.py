from django.contrib import admin

from .models import KnowledgeRule


@admin.register(KnowledgeRule)
class KnowledgeRuleAdmin(admin.ModelAdmin):
    list_display = ("kind", "priority", "is_active", "created_at")
    list_filter = ("kind", "is_active")
    search_fields = ("recommendation",)
    readonly_fields = ("created_at", "updated_at")
