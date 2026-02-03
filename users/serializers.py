from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from .models import User


class UserSerializer(serializers.ModelSerializer):
    rating = serializers.SerializerMethodField(method_name='get_rating')

    def get_rating(self, obj):
        rating = obj.rating
        if rating:
            return {
                'score': rating.score,
                'matches_played': rating.matches_played,
                'matches_won': rating.matches_won,
                'matches_lost': rating.matches_lost,
                'matches_drawn': rating.matches_drawn
            }
        return {}
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', "rating"]
        read_only_fields = ['id', "rating"]


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        super().validate(attrs)
        try:
            refresh_token = RefreshToken(attrs['refresh'])
            user = User.objects.get(id=refresh_token.payload['user_id'])
            if user.is_active == False:
                raise serializers.ValidationError("Аккаунт отключён! Обратитесь к админам:)")
            access_token = refresh_token.access_token
            return {
                'access': str(access_token),
                'refresh': attrs['refresh']
            }
        except TokenError:
            raise serializers.ValidationError("Неверный refresh токен!")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'password', 'password2']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password": "Не указан пароль!"
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True, required=True, style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                raise serializers.ValidationError("Неверный логин или пароль!")
            
            if not user.is_active:
                raise serializers.ValidationError("Аккаунт отключён! Обратитесь к админам:)")

            auth_user = authenticate(username=user.username, password=password)
            if not auth_user:
                raise serializers.ValidationError("Неверный логин или пароль!")
        else:
            raise serializers.ValidationError("Must include 'email' and 'password'")
        
        attrs['user'] = auth_user
        return attrs