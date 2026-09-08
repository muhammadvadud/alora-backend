from typing import Any
from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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
