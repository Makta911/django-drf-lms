from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import Payment
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    PaymentSerializer,
    PaymentDetailSerializer
)
from .permissions import IsOwnerOrAdmin, IsOwnerOrModerator

User = get_user_model()


# Кастомный сериализатор для токенов
class CustomTokenObtainPairSerializer(serializers.Serializer):
    """Кастомный сериализатор для получения токенов"""
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('Неверный email или пароль')

        if not user.check_password(password):
            raise serializers.ValidationError('Неверный email или пароль')

        if not user.is_active:
            raise serializers.ValidationError('Пользователь неактивен')

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data
        }


class CustomTokenObtainPairView(TokenObtainPairView):
    """Кастомный вью для получения JWT токенов"""
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]


class UserRegistrationAPIView(generics.CreateAPIView):
    """Регистрация нового пользователя"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]


class UserListAPIView(generics.ListAPIView):
    """Список пользователей (только для админов)"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Детальное представление пользователя"""
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Изменять/удалять может только владелец или админ
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """Профиль текущего пользователя"""
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class PaymentListAPIView(generics.ListAPIView):
    """Представление для списка платежей с фильтрацией"""
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'lesson', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Фильтрация платежей по правам доступа"""
        user = self.request.user

        # Админы и модераторы видят все платежи
        if user.is_staff or user.is_superuser or user.groups.filter(name='moderators').exists():
            return Payment.objects.all()

        # Обычные пользователи видят только свои платежи
        return Payment.objects.filter(user=user)


class PaymentRetrieveAPIView(generics.RetrieveAPIView):
    """Представление для детального просмотра платежа"""
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]