"""Suhbat filtrlari."""

import django_filters

from apps.chat.models import Conversation


class ConversationFilter(django_filters.FilterSet):
    class Meta:
        model = Conversation
        fields = ("status", "stage", "mode")
