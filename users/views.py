from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample, extend_schema_view
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, RefreshSerializer
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
        },
        tags=["Auth"],
        auth=[]
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = LoginSerializer

    @extend_schema(
        summary="Авторизация пользователя",
        description="Получение acess/refresh токенов при авторизации",
        responses={
            200: OpenApiResponse(
                Response({
                    'access': "string",
                    'refresh': "string",
                    'user': UserSerializer()
                }), examples=[
                    OpenApiExample(name="Успешно", value={
                        'access': "string",
                        'refresh': "string",
                        'user': {}
                    })
                ]
            ),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Auth"],
        auth=[]
    )
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


class RefreshTokenView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RefreshSerializer

    @extend_schema(
        summary="Обновление токена доступа",
        description="Передача refresh токена, получение нового токена доступа",
        responses={
            200: OpenApiResponse(
                Response({'access': 'string'}), examples=[
                    OpenApiExample(name="Успешно", value={'access': 'string'})
                ]
            ),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Auth"],
        auth=[]
    )
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
    
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema_view(
    get=extend_schema(
        summary="Получение информации о пользователе",
        description="Получение информации о пользователе",
        responses={
            200: UserSerializer(),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Auth"],
    ),
    put=extend_schema(
        summary="Обновление информации о пользователе (обновление всех полей)",
        description="Обновление информации о пользователе",
        responses={
            200: UserSerializer(),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Auth"],
    ),
    patch=extend_schema(
        summary="Обновление информации о пользователе (конкретные поля)",
        description="Обновление информации о пользователе",
        responses={
            200: UserSerializer(),
            400: OpenApiResponse(description="Validation error")
        },
        tags=["Auth"],
    )
)
class UserView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
