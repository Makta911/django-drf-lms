from rest_framework import serializers
from .models import Payment
from lms.serializers import CourseSerializer, LessonSerializer
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

User = get_user_model()

class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('payment_date',)


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения платежа"""
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователя"""
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'password', 'is_active']
        read_only_fields = ['id', 'is_active']

    def create(self, validated_data):
        """Создание пользователя с хешированием пароля"""
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        """Обновление пользователя с хешированием пароля"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя"""
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'city', 'password', 'password_confirm', 'tokens']
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
        }

    def validate(self, attrs):
        """Проверка пароля и подтверждения"""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Пароли не совпадают"})
        return attrs

    def validate_email(self, value):
        """Проверка уникальности email"""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value

    def create(self, validated_data):
        """Создание пользователя"""
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

    def get_tokens(self, obj):
        """Получение токенов JWT"""
        refresh = RefreshToken.for_user(obj)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для профиля пользователя"""

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'city', 'avatar', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Кастомный сериализатор для получения токенов с email"""

    username_field = 'email'  # Используем email вместо username

    def validate(self, attrs):
        # Вызываем родительский метод, но с email
        data = super().validate(attrs)

        # Добавляем информацию о пользователе в ответ
        data['user'] = UserSerializer(self.user).data
        return data

    @classmethod
    def get_token(cls, user):
        """Создание токена с кастомными claims"""
        token = super().get_token(user)

        # Добавляем кастомные данные в токен
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['is_staff'] = user.is_staff
        token['is_superuser'] = user.is_superuser

        return token