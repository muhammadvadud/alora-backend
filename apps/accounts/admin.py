from django.contrib import admin

from .models import Tenant, User


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "phone")
    readonly_fields = ("created_at", "updated_at")


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("phone", "tenant", "role", "full_name", "is_active")
    list_filter = ("role", "is_active", "tenant")
    search_fields = ("phone", "full_name")
    readonly_fields = ("created_at", "updated_at")
