from django.contrib import admin

from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ("created_at", "updated_at")


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "tenant", "is_active", "created_at")
    list_filter = ("is_active", "tenant")
    search_fields = ("title", "session_id")
    readonly_fields = ("created_at", "updated_at")
    inlines = [MessageInline]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("content",)
    readonly_fields = ("created_at", "updated_at")
