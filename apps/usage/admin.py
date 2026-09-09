from django.contrib import admin

from .models import UsageDaily, UsageLimit, UsageRecord


@admin.register(UsageRecord)
class UsageRecordAdmin(admin.ModelAdmin):
    list_display = ("user", "tenant", "prompt_tokens", "completion_tokens", "cost_uzs", "created_at")
    list_filter = ("tenant", "created_at")
    search_fields = ("user__phone",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(UsageDaily)
class UsageDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "user", "tenant", "tokens", "cost_uzs")
    list_filter = ("date", "tenant")
    search_fields = ("user__phone",)
    readonly_fields = ("created_at", "updated_at")

@admin.register(UsageLimit)
class UsageLimitAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "max_cost_uzs", "max_tokens", "is_active")
    list_filter = ("role", "is_active")
    search_fields = ("user__phone",)
    readonly_fields = ("created_at", "updated_at")
