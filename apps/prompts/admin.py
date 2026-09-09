from django.contrib import admin

from .models import PromptVersion


@admin.register(PromptVersion)
class PromptVersionAdmin(admin.ModelAdmin):
    list_display = ("version", "author", "is_current", "created_at")
    list_filter = ("is_current",)
    readonly_fields = ("created_at", "updated_at")
