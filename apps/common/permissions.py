"""Rol asosidagi permission'lar."""

from __future__ import annotations

from typing import Any

from rest_framework.permissions import IsAuthenticated

from .choices import UserRole

ROLE_RANK: dict[str, int] = {
    UserRole.EMPLOYEE: 1,
    UserRole.MANAGER: 2,
    UserRole.ADMIN: 3,
}


def _role_rank(user: Any) -> int:
    """Foydalanuvchi rolini iyerarxik ballga aylantiradi."""

    role = getattr(user, "role", None)
    if not isinstance(role, str):
        return 0
    return ROLE_RANK.get(role, 0)


class IsEmployee(IsAuthenticated):
    """Xodim, menejer yoki admin kirishi mumkin."""

    def has_permission(self, request: Any, view: Any) -> bool:
        return (
            super().has_permission(request, view)
            and _role_rank(request.user) >= ROLE_RANK[UserRole.EMPLOYEE]
        )


class IsManager(IsAuthenticated):
    """Menejer yoki admin kirishi mumkin."""

    def has_permission(self, request: Any, view: Any) -> bool:
        return (
            super().has_permission(request, view)
            and _role_rank(request.user) >= ROLE_RANK[UserRole.MANAGER]
        )


class IsAdmin(IsAuthenticated):
    """Faqat admin kirishi mumkin."""

    def has_permission(self, request: Any, view: Any) -> bool:
        return (
            super().has_permission(request, view)
            and _role_rank(request.user) >= ROLE_RANK[UserRole.ADMIN]
        )


class IsOwnerOrManager(IsAuthenticated):
    """Obyekt egasi yoki menejer/admin uchun ruxsat beradi."""

    def has_object_permission(self, request: Any, view: Any, obj: Any) -> bool:
        if _role_rank(request.user) >= ROLE_RANK[UserRole.MANAGER]:
            return True

        owner = _resolve_owner(obj)
        if owner is None:
            return False

        return getattr(owner, "pk", None) == getattr(request.user, "pk", None)


def _resolve_owner(obj: Any) -> Any | None:
    """Obyekt egasini topadi."""

    for attribute_name in ("user", "owner", "created_by"):
        owner = getattr(obj, attribute_name, None)
        if owner is not None:
            return owner
    return None
