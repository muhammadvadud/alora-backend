import pytest

from apps.accounts.admin import UserAdminForm
from apps.common.factories import UserFactory


@pytest.mark.django_db
def test_admin_form_sets_new_password():
    user = UserFactory(password="old-password-123")

    form = UserAdminForm(
        instance=user,
        data={
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role,
            "password": "new-password-123",
            "password_confirmation": "new-password-123",
        },
    )

    assert form.is_valid(), form.errors
    form.save()
    user.refresh_from_db()

    assert user.check_password("new-password-123")
    assert not user.check_password("old-password-123")


@pytest.mark.django_db
def test_admin_form_keeps_password_when_fields_are_empty():
    user = UserFactory(password="old-password-123")

    form = UserAdminForm(
        instance=user,
        data={
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role,
            "password": "",
            "password_confirmation": "",
        },
    )

    assert form.is_valid(), form.errors
    form.save()
    user.refresh_from_db()

    assert user.check_password("old-password-123")


@pytest.mark.django_db
def test_admin_form_rejects_different_password_confirmation():
    user = UserFactory(password="old-password-123")
    form = UserAdminForm(
        instance=user,
        data={
            "phone": user.phone,
            "full_name": user.full_name,
            "role": user.role,
            "password": "new-password-123",
            "password_confirmation": "different-password-123",
        },
    )

    assert not form.is_valid()
    assert "bir xil" in str(form.errors)
