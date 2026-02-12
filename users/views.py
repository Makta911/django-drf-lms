from rest_framework import generics, permissions, status, serializers
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
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
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


# Кастомный сериализатор для токенов
class CustomTokenObtainPairSerializer(serializers.Serializer):
    """
    Сериализатор для получения JWT токенов по email.

    Fields:
    - email: Email пользователя (обязательное поле)
    - password: Пароль пользователя (обязательное поле, write-only)

    Returns:
    - refresh: Refresh JWT token
    - access: Access JWT token
    - user: Информация о пользователе
    """
    email = serializers.EmailField(
        help_text="Email пользователя для аутентификации"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        help_text="Пароль пользователя"
    )

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
    """
    API для получения JWT токенов.

    Не требует аутентификации.
    Использует email вместо username.
    """
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Получение JWT токенов по email и паролю",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='email',
                    description='Email пользователя'
                ),
                'password': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    format='password',
                    description='Пароль пользователя'
                )
            }
        ),
        responses={
            200: openapi.Response(
                description="Токены получены",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                        'access': openapi.Schema(type=openapi.TYPE_STRING),
                        'user': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                                'email': openapi.Schema(type=openapi.TYPE_STRING),
                                'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                                'last_name': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: "Неверные учетные данные"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserRegistrationAPIView(generics.CreateAPIView):
    """
    API для регистрации нового пользователя.

    Не требует аутентификации.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        operation_description="Регистрация нового пользователя",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Пользователь создан",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'email': openapi.Schema(type=openapi.TYPE_STRING),
                        'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                        'tokens': openapi.Schema(
                            type=openapi.TYPE_OBJECT,
                            properties={
                                'refresh': openapi.Schema(type=openapi.TYPE_STRING),
                                'access': openapi.Schema(type=openapi.TYPE_STRING)
                            }
                        )
                    }
                )
            ),
            400: "Неверные данные или email уже существует"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserListAPIView(generics.ListAPIView):
    """
    API для получения списка пользователей.

    Требуется аутентификация через JWT токен.
    Доступ: только администраторы.

    Возвращает список всех пользователей в системе.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAdminUser]

    @swagger_auto_schema(
        operation_description="Получить список всех пользователей (только для администраторов)",
        manual_parameters=[
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Размер страницы",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: UserSerializer(many=True),
            403: "Нет прав администратора"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    API для управления пользователем (детальный просмотр, обновление, удаление).

    Требуется аутентификация через JWT токен.

    Права доступа:
    - GET: Любой аутентифицированный пользователь может просматривать любого пользователя
    - PUT/PATCH: Только владелец профиля или администратор
    - DELETE: Только владелец профиля или администратор
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @swagger_auto_schema(
        operation_description="Получить информацию о пользователе",
        responses={
            200: UserSerializer,
            401: "Требуется аутентификация",
            403: "Нет прав доступа",
            404: "Пользователь не найден"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Полное обновление информации о пользователе (только владелец или администратор)",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Неверные данные",
            401: "Требуется аутентификация",
            403: "Нет прав для обновления",
            404: "Пользователь не найден"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление информации о пользователе (только владелец или администратор)",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: "Неверные данные",
            401: "Требуется аутентификация",
            403: "Нет прав для обновления",
            404: "Пользователь не найден"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить пользователя (только владелец или администратор)",
        responses={
            204: "Пользователь успешно удален",
            401: "Требуется аутентификация",
            403: "Нет прав для удаления",
            404: "Пользователь не найден"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_permissions(self):
        """Разные права для разных методов"""
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            # Изменять/удалять может только владелец или админ
            return [permissions.IsAuthenticated(), IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    API для получения и обновления профиля текущего пользователя.

    Требуется аутентификация через JWT токен.
    Возвращает информацию о текущем аутентифицированном пользователе.

    Особенности:
    - Автоматически определяет текущего пользователя
    - Не требует указания ID пользователя
    - Доступен только владельцу профиля
    """
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить профиль текущего пользователя",
        responses={
            200: UserProfileSerializer,
            401: "Требуется аутентификация"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Полное обновление профиля текущего пользователя",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: "Неверные данные",
            401: "Требуется аутентификация"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление профиля текущего пользователя",
        request_body=UserProfileSerializer,
        responses={
            200: UserProfileSerializer,
            400: "Неверные данные",
            401: "Требуется аутентификация"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        """Возвращает текущего аутентифицированного пользователя"""
        return self.request.user

class PaymentListAPIView(generics.ListAPIView):
    """
    API для получения списка платежей.

    Требуется аутентификация через JWT токен.
    Пользователи видят только свои платежи.
    Администраторы и модераторы видят все платежи.

    Доступна фильтрация и сортировка:
    - Фильтрация: по курсу, уроку, способу оплаты
    - Сортировка: по дате оплаты (возрастание/убывание)
    """
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'lesson', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить список платежей",
        manual_parameters=[
            openapi.Parameter(
                'course',
                openapi.IN_QUERY,
                description="Фильтр по ID курса",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'lesson',
                openapi.IN_QUERY,
                description="Фильтр по ID урока",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'payment_method',
                openapi.IN_QUERY,
                description="Фильтр по способу оплаты (cash/transfer)",
                type=openapi.TYPE_STRING,
                enum=['cash', 'transfer']
            ),
            openapi.Parameter(
                'ordering',
                openapi.IN_QUERY,
                description="Сортировка по дате оплаты (payment_date или -payment_date)",
                type=openapi.TYPE_STRING
            ),
            openapi.Parameter(
                'page',
                openapi.IN_QUERY,
                description="Номер страницы",
                type=openapi.TYPE_INTEGER
            ),
            openapi.Parameter(
                'page_size',
                openapi.IN_QUERY,
                description="Размер страницы",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: PaymentSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class PaymentRetrieveAPIView(generics.RetrieveAPIView):
    """
    API для получения детальной информации о платеже.

    Требуется аутентификация через JWT токен.
    Доступ: владелец платежа, модератор или администратор.

    Возвращает полную информацию о платеже, включая связанные
    объекты курса и урока (если применимо).
    """
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о платеже",
        responses={
            200: openapi.Response(
                description="Информация о платеже",
                schema=PaymentDetailSerializer
            ),
            403: openapi.Response(
                description="Нет прав доступа",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Сообщение об ошибке прав доступа'
                        )
                    }
                )
            ),
            404: openapi.Response(
                description="Платеж не найден",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'detail': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='Платеж с указанным ID не существует'
                        )
                    }
                )
            )
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

