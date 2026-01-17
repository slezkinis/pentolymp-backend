from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiResponse

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer
    
    @extend_schema(
        summary="Регистрация пользователя",
        description="Создание нового пользователя",
        responses={
            201: UserSerializer(),
            400: OpenApiResponse(description="Validation error")
        }
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer


    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            user_serializer = UserSerializer(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': user_serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)