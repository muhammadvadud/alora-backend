"""Umumiy bazaviy modellar va queryset mixinlari."""

from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import FieldDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """UUID asosidagi umumiy model bazasi."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name=_("Yaratildi"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilandi"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("Faol"))

    class Meta:
        abstract = True
        ordering = ("-created_at",)


class TenantScopedModel(BaseModel):
    """Tenant bilan bog'langan bazaviy model."""

    tenant = models.ForeignKey(
        "accounts.Tenant",
        on_delete=models.PROTECT,
        related_name="%(class)s_set",
        db_index=True,
        verbose_name=_("Ijarachi"),
    )

    class Meta:
        abstract = True


class TenantScopedQuerySetMixin:
    """ViewSet queryset'ini avtomatik tenant bo'yicha cheklaydi."""

    def get_queryset(self) -> Any:
        """Request dagi tenant asosida queryset ni filtrlaydi (fail-closed)."""
        queryset = super().get_queryset()
        if queryset is None:
            return queryset
        model = getattr(queryset, "model", None)
        if model is None or not self._has_tenant_field(model):
            return queryset
        user = getattr(self.request, "user", None)
        tenant_id = getattr(user, "tenant_id", None)
        # Tenant aniqlanmasa — hech narsa ko'rsatilmaydi (ochiq qoldirilmaydi).
        if tenant_id is None:
            return queryset.none()
        return queryset.filter(tenant_id=tenant_id)

    @staticmethod
    def _has_tenant_field(model: type[Any]) -> bool:
        """Model tarkibida `tenant` maydoni borligini tekshiradi."""

        meta = getattr(model, "_meta", None)
        if meta is None:
            return False
        try:
            meta.get_field("tenant")
        except FieldDoesNotExist:
            return False
        return True

