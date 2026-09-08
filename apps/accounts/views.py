from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from apps.accounts.serializers import CustomTokenObtainPairSerializer, AuthMeSerializer

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # 5/daqiqa rate limit throttling settings da bo'lishi kerak yoki shu yerda beriladi.
    throttle_scope = "login"

class AuthMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        serializer = AuthMeSerializer(request.user)
        return Response(serializer.data)
