from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer, SubscriptionSerializer
from users.permissions import IsOwnerOrModerator, IsModerator, IsOwner
from .paginators import CoursePagination, LessonPagination, SubscriptionPagination
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class CourseViewSet(viewsets.ModelViewSet):
    """
    API для управления курсами.

    Позволяет выполнять CRUD операции с курсами.
    Требуется аутентификация через JWT токен.

    Права доступа:
    - Администраторы: полный доступ
    - Модераторы: только просмотр и редактирование
    - Владельцы: полный доступ к своим курсам
    - Обычные пользователи: только просмотр своих курсов
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = CoursePagination

    @swagger_auto_schema(
        operation_description="Получить список курсов",
        responses={200: CourseSerializer(many=True)}
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый курс",
        request_body=CourseSerializer,
        responses={
            201: CourseSerializer,
            400: "Неверные данные",
            403: "Нет прав для создания курса"
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Получить детальную информацию о курсе",
        responses={
            200: CourseSerializer,
            404: "Курс не найден"
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Обновить курс",
        request_body=CourseSerializer,
        responses={
            200: CourseSerializer,
            400: "Неверные данные",
            403: "Нет прав для обновления",
            404: "Курс не найден"
        }
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частично обновить курс",
        request_body=CourseSerializer,
        responses={
            200: CourseSerializer,
            400: "Неверные данные",
            403: "Нет прав для обновления",
            404: "Курс не найден"
        }
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Удалить курс",
        responses={
            204: "Курс удален",
            403: "Нет прав для удаления",
            404: "Курс не найден"
        }
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class LessonListCreateView(generics.ListCreateAPIView):
    """
    API для получения списка уроков и создания новых уроков.

    Требуется аутентификация через JWT токен.
    Создавать уроки могут только владельцы курсов (не модераторы).
    """
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = LessonPagination

    @swagger_auto_schema(
        operation_description="Получить список уроков",
        manual_parameters=[
            openapi.Parameter(
                'course',
                openapi.IN_QUERY,
                description="Фильтр по ID курса",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={200: LessonSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Создать новый урок",
        request_body=LessonSerializer,
        responses={
            201: LessonSerializer,
            400: "Неверные данные или не YouTube ссылка",
            403: "Нет прав для создания урока"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LessonRetrieveView(generics.RetrieveAPIView):
    """
    API для получения детальной информации об уроке.

    Требуется аутентификация через JWT токен.
    Доступ: владелец урока или модератор.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]

    @swagger_auto_schema(
        operation_description="Получить детальную информацию об уроке",
        responses={
            200: LessonSerializer,
            403: "Нет прав доступа к уроку",
            404: "Урок не найден"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LessonUpdateView(generics.UpdateAPIView):
    """
    API для обновления урока.

    Требуется аутентификация через JWT токен.
    Доступ: владелец урока или модератор.

    Примечание: при обновлении видео-ссылки применяется валидатор YouTube.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]

    @swagger_auto_schema(
        operation_description="Полное обновление урока",
        request_body=LessonSerializer,
        responses={
            200: LessonSerializer,
            400: "Неверные данные или не YouTube ссылка",
            403: "Нет прав для обновления урока",
            404: "Урок не найден"
        }
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Частичное обновление урока",
        request_body=LessonSerializer,
        responses={
            200: LessonSerializer,
            400: "Неверные данные или не YouTube ссылка",
            403: "Нет прав для обновления урока",
            404: "Урок не найден"
        }
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


class LessonDestroyView(generics.DestroyAPIView):
    """
    API для удаления урока.

    Требуется аутентификация через JWT токен.
    Доступ: только владелец урока (модераторы не могут удалять).
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    @swagger_auto_schema(
        operation_description="Удалить урок",
        responses={
            204: "Урок успешно удален",
            403: "Нет прав для удаления урока (только владелец)",
            404: "Урок не найден"
        }
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)

    def get_permissions(self):
        """Удалять может только владелец (не модератор!)"""
        return [permissions.IsAuthenticated(), IsOwner()]

    def perform_destroy(self, instance):
        """Проверка прав перед удалением"""
        user = self.request.user

        # Модераторы не могут удалять уроки
        if user.groups.filter(name='moderators').exists():
            raise PermissionDenied("Модераторы не могут удалять уроки")

        # Владелец удаляет свой урок
        if instance.owner == user:
            instance.delete()
        else:
            raise PermissionDenied("У вас нет прав для удаления этого урока")


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    API для управления подписками на курсы.

    Позволяет подписываться и отписываться от курсов.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = SubscriptionPagination

    @swagger_auto_schema(
        operation_description="Подписаться на курс",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_id'],
            properties={
                'course_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID курса для подписки'
                )
            }
        ),
        responses={
            201: SubscriptionSerializer,
            400: "Не указан course_id",
            404: "Курс не найден"
        }
    )
    @action(detail=False, methods=['post'])
    def subscribe(self, request):
        """Подписаться на курс"""
        from .models import Subscription, Course

        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {'error': 'Не указан course_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response(
                {'error': 'Курс не найден'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Проверяем существующую подписку
        subscription, created = Subscription.objects.get_or_create(
            user=request.user,
            course=course,
            defaults={'is_active': True}
        )

        if not created:
            # Если подписка уже существует, активируем ее
            subscription.is_active = True
            subscription.save()

        serializer = self.get_serializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        operation_description="Отписаться от курса",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['course_id'],
            properties={
                'course_id': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description='ID курса для отписки'
                )
            }
        ),
        responses={
            200: "Вы успешно отписались от курса",
            400: "Не указан course_id",
            404: "Активная подписка не найдена"
        }
    )
    @action(detail=False, methods=['post'])
    def unsubscribe(self, request):
        """Отписаться от курса"""
        from .models import Subscription

        course_id = request.data.get('course_id')

        if not course_id:
            return Response(
                {'error': 'Не указан course_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            subscription = Subscription.objects.get(
                user=request.user,
                course_id=course_id,
                is_active=True
            )
        except Subscription.DoesNotExist:
            return Response(
                {'error': 'Активная подписка не найдена'},
                status=status.HTTP_404_NOT_FOUND
            )

        subscription.is_active = False
        subscription.save()

        return Response(
            {'message': 'Вы успешно отписались от курса'},
            status=status.HTTP_200_OK
        )