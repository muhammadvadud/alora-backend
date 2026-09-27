from typing import Any

from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from apps.common.choices import OnExceed, UsagePeriod, UserRole

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user: Any) -> Any:
        token = super().get_token(user)
        token["user_id"] = str(user.id)
        token["role"] = user.role
        token["tenant_id"] = str(user.tenant.id) if user.tenant else None
        return token


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "phone", "full_name", "role", "tenant", "device_id")
        read_only_fields = fields


class AuthMeSerializer(serializers.Serializer):
    profile = UserProfileSerializer(source="*")
    limit = serializers.DictField(default=None)


class EmployeeListSerializer(serializers.ModelSerializer):
    """Xodimlar ro'yxati uchun o'qish serializer'i."""

    today_tokens = serializers.IntegerField(read_only=True, default=0)
    today_messages = serializers.IntegerField(read_only=True, default=0)
    today_conversations = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = User
        fields = (
            "id",
            "phone",
            "full_name",
            "role",
            "is_active",
            "last_login",
            "created_at",
            "today_tokens",
            "today_messages",
            "today_conversations",
        )
        read_only_fields = ("id", "last_login", "created_at")


class EmployeeWriteSerializer(serializers.ModelSerializer):
    """Xodim qo'shish uchun yozish serializer'i."""

    password = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={"input_type": "password"}
    )

    class Meta:
        model = User
        fields = ("phone", "full_name", "password", "role", "is_active", "device_id")
        extra_kwargs = {
            "phone": {"required": True},
            "full_name": {"required": True},
            "role": {"required": False},
            "is_active": {"required": False},
        }

    def validate_role(self, value: str) -> str:
        # Jamoa paneli admin yaratmaydi va admin'ga ko'tarmaydi: aks holda manager
        # o'zini yoki yangi akkauntni admin qilib, tenantni to'liq egallardi.
        if value == UserRole.ADMIN:
            raise serializers.ValidationError("Admin rolini jamoa panelidan berib bo'lmaydi.")
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        request = self.context.get("request")
        is_self = (
            self.instance is not None
            and request is not None
            and self.instance.pk == request.user.pk
        )
        # O'z rolini/holatini o'zgartirish — imtiyoz oshirish yoki o'zini bloklab qo'yish yo'li.
        if is_self and ({"role", "is_active"} & attrs.keys()):
            raise serializers.ValidationError(
                "O'z rolingiz yoki holatingizni jamoa panelidan o'zgartira olmaysiz."
            )
        return attrs

    def create(self, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password", None)
        user = User.objects.create_user(**validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user

    def update(self, instance: User, validated_data: dict[str, Any]) -> User:
        password = validated_data.pop("password", None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        if password:
            instance.set_password(password)
            instance.save(update_fields=["password"])
        return instance


class EmployeeLimitSerializer(serializers.Serializer):
    """Xodim limitini o'rnatish uchun serializer.

    `is_unlimited` true berilsa cheklov umuman qo'llanmaydi.
    """

    is_unlimited = serializers.BooleanField(required=False)
    period = serializers.ChoiceField(choices=UsagePeriod.choices, required=False)
    max_tokens = serializers.IntegerField(required=False, min_value=0, allow_null=True)
    max_cost_uzs = serializers.DecimalField(
        max_digits=14, decimal_places=2, min_value=0, required=False, allow_null=True
    )
    max_messages = serializers.IntegerField(required=False, min_value=0, allow_null=True)
    on_exceed = serializers.ChoiceField(choices=OnExceed.choices, required=False)
    is_active = serializers.BooleanField(required=False)


class EmployeePasswordSerializer(serializers.Serializer):
    """Xodim parolini almashtirish uchun yozish serializer'i."""

    password = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )
    password_confirmation = serializers.CharField(
        write_only=True, min_length=8, style={"input_type": "password"}
    )

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "Parollar bir xil bo'lishi kerak."}
            )
        password_validation.validate_password(attrs["password"], self.context.get("user"))
        return attrs

    def save(self, **kwargs: Any) -> User:
        user = self.context["user"]
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])
        return user
