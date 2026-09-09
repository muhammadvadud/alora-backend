"""Buyurtma filtr qatlami (8.9)."""

from __future__ import annotations

from typing import ClassVar

import django_filters
from django.db.models import Q, QuerySet

from apps.common.choices import OrderStatus
from apps.orders.models import Order


class OrderFilter(django_filters.FilterSet):
    """Buyurtma ro'yxat uchun filtr va qidiruv."""

    status = django_filters.ChoiceFilter(choices=OrderStatus.choices)
    user = django_filters.UUIDFilter(field_name="user_id")
    date = django_filters.DateFilter(field_name="created_at", lookup_expr="date")
    date_from = django_filters.DateFilter(field_name="created_at", lookup_expr="date__gte")
    date_to = django_filters.DateFilter(field_name="created_at", lookup_expr="date__lte")
    search = django_filters.CharFilter(method="filter_search")

    class Meta:
        model = Order
        fields: ClassVar[list[str]] = ["status", "user"]

    def filter_search(self, queryset: QuerySet[Order], name: str, value: str) -> QuerySet[Order]:
        """Raqam, mijoz ismi yoki telefon bo'yicha qidiradi."""

        return queryset.filter(
            Q(number__icontains=value)
            | Q(customer_name__icontains=value)
            | Q(customer_phone__icontains=value)
        )