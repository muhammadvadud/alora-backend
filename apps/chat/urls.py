"""Suhbat uchun URL konfiguratsiyasi."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.chat.views import ConversationMessagesView, ConversationViewSet

app_name = "chat"

router = DefaultRouter()
router.register("conversations", ConversationViewSet, basename="conversation")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "conversations/<str:pk>/messages/",
        ConversationMessagesView.as_view(),
        name="conversation-messages-stream",
    ),
]
