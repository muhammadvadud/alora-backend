from __future__ import annotations

from types import SimpleNamespace

from django.core.exceptions import FieldDoesNotExist

from apps.common.models import TenantScopedQuerySetMixin


class DummyField:
    """Tenant maydonini ifodalovchi bo'sh obyekt."""


class DummyMeta:
    """Model `_meta` o'rnini bosuvchi minimal sinf."""

    def __init__(self, has_tenant: bool) -> None:
        self.has_tenant = has_tenant

    def get_field(self, name: str) -> DummyField:
        if name != "tenant" or not self.has_tenant:
            raise FieldDoesNotExist(name)
        return DummyField()


class DummyModel:
    """Tenant maydoni bor model."""

    _meta = DummyMeta(has_tenant=True)


class DummyQuerySet:
    """Filtrlash chaqiruvlarini yozib boradigan soddalashtirilgan queryset."""

    def __init__(self, model: type[object]) -> None:
        self.model = model
        self.filters: list[dict[str, object]] = []

    def filter(self, **kwargs: object) -> "DummyQuerySet":
        self.filters.append(kwargs)
        return self


class BaseView:
    """Mixin uchun minimal view bazasi."""

    def __init__(self, queryset: DummyQuerySet) -> None:
        self._queryset = queryset

    def get_queryset(self) -> DummyQuerySet:
        return self._queryset


class ScopedView(TenantScopedQuerySetMixin, BaseView):
    """TenantScopedQuerySetMixin tekshiruvi uchun view."""


def test_tenant_scoped_queryset_filters_by_request_tenant(tenant: object) -> None:
    queryset = DummyQuerySet(DummyModel)
    view = ScopedView(queryset)
    view.request = SimpleNamespace(user=SimpleNamespace(tenant=tenant, tenant_id=None))

    result = view.get_queryset()

    assert result.filters == [{"tenant": tenant}]


def test_tenant_scoped_queryset_leaves_queryset_unchanged_when_no_tenant_field() -> None:
    class NoTenantModel:
        _meta = DummyMeta(has_tenant=False)

    queryset = DummyQuerySet(NoTenantModel)
    view = ScopedView(queryset)
    tenant = SimpleNamespace(id=1)
    view.request = SimpleNamespace(user=SimpleNamespace(tenant=tenant, tenant_id=None))

    result = view.get_queryset()

    assert result is queryset
    assert result.filters == []

