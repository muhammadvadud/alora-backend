from __future__ import annotations

from types import SimpleNamespace

from apps.common.choices import UserRole
from apps.common.permissions import IsAdmin, IsEmployee, IsManager, IsOwnerOrManager


def _request(user: object) -> SimpleNamespace:
    return SimpleNamespace(user=user)


def _user(role: str, pk: int = 1) -> SimpleNamespace:
    return SimpleNamespace(pk=pk, role=role, is_authenticated=True)


def test_is_employee_allows_all_roles() -> None:
    permission = IsEmployee()

    assert permission.has_permission(_request(_user(UserRole.EMPLOYEE)), None) is True
    assert permission.has_permission(_request(_user(UserRole.MANAGER)), None) is True
    assert permission.has_permission(_request(_user(UserRole.ADMIN)), None) is True


def test_is_manager_requires_manager_or_admin() -> None:
    permission = IsManager()

    assert permission.has_permission(_request(_user(UserRole.EMPLOYEE)), None) is False
    assert permission.has_permission(_request(_user(UserRole.MANAGER)), None) is True
    assert permission.has_permission(_request(_user(UserRole.ADMIN)), None) is True


def test_is_admin_allows_only_admin() -> None:
    permission = IsAdmin()

    assert permission.has_permission(_request(_user(UserRole.EMPLOYEE)), None) is False
    assert permission.has_permission(_request(_user(UserRole.MANAGER)), None) is False
    assert permission.has_permission(_request(_user(UserRole.ADMIN)), None) is True


def test_is_owner_or_manager_allows_owner_and_manager() -> None:
    permission = IsOwnerOrManager()
    owner = _user(UserRole.EMPLOYEE, pk=11)
    other_employee = _user(UserRole.EMPLOYEE, pk=22)
    manager = _user(UserRole.MANAGER, pk=33)
    admin = _user(UserRole.ADMIN, pk=44)
    obj = SimpleNamespace(user=owner)

    assert permission.has_object_permission(_request(owner), None, obj) is True
    assert permission.has_object_permission(_request(other_employee), None, obj) is False
    assert permission.has_object_permission(_request(manager), None, obj) is True
    assert permission.has_object_permission(_request(admin), None, obj) is True
