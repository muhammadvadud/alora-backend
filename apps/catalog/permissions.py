"""Katalog uchun ruxsatlar."""

from typing import Any

from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from apps.common.choices import UserRole
from apps.common.permissions import ROLE_RANK, _role_rank


class IsManagerOrReadOnly(IsAuthenticated):
    """
    O'qish (GET, HEAD, OPTIONS) barcha autentifikatsiyadan o'tganlarga (shu jumladan xodimlarga),
    yozish (POST, PUT, PATCH, DELETE) faqat menejer va admin uchun.
    """

    def has_permission(self, request: Any, view: Any) -> bool:
        if not super().has_permission(request, view):
            return False
            
        if request.method in SAFE_METHODS:
            return True
            
        return _role_rank(request.user) >= ROLE_RANK[UserRole.MANAGER]
