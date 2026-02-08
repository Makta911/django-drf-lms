from rest_framework import viewsets, generics, permissions
from rest_framework.exceptions import PermissionDenied
from .models import Course, Lesson
from .serializers import CourseSerializer, LessonSerializer
from users.permissions import IsOwnerOrModerator, IsModerator, IsOwner


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet для курсов (CRUD) с проверкой прав"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Фильтрация курсов по правам доступа"""
        user = self.request.user

        # Админы видят все
        if user.is_staff or user.is_superuser:
            return Course.objects.all()

        # Модераторы видят все
        if user.groups.filter(name='moderators').exists():
            return Course.objects.all()

        # Обычные пользователи видят только свои курсы
        return Course.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании курса устанавливаем владельца"""
        # Модераторы не могут создавать курсы
        if self.request.user.groups.filter(name='moderators').exists():
            raise PermissionDenied("Модераторы не могут создавать курсы")
        serializer.save(owner=self.request.user)

    def perform_update(self, serializer):
        """При обновлении курса проверяем права"""
        instance = self.get_object()
        user = self.request.user

        # Модераторы могут обновлять любые курсы
        if user.groups.filter(name='moderators').exists():
            serializer.save()
        # Владелец обновляет свой курс
        elif instance.owner == user:
            serializer.save()
        else:
            raise PermissionDenied("У вас нет прав для редактирования этого курса")

    def perform_destroy(self, instance):
        """При удалении курса проверяем права"""
        user = self.request.user

        # Модераторы не могут удалять курсы
        if user.groups.filter(name='moderators').exists():
            raise PermissionDenied("Модераторы не могут удалять курсы")

        # Владелец удаляет свой курс
        if instance.owner == user:
            instance.delete()
        else:
            raise PermissionDenied("У вас нет прав для удаления этого курса")


class LessonListCreateView(generics.ListCreateAPIView):
    """Получение списка уроков и создание нового"""
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Фильтрация уроков по правам доступа"""
        user = self.request.user

        # Админы видят все
        if user.is_staff or user.is_superuser:
            return Lesson.objects.all()

        # Модераторы видят все
        if user.groups.filter(name='moderators').exists():
            return Lesson.objects.all()

        # Обычные пользователи видят только свои уроки
        return Lesson.objects.filter(owner=user)

    def perform_create(self, serializer):
        """При создании урока устанавливаем владельца"""
        # Модераторы не могут создавать уроки
        if self.request.user.groups.filter(name='moderators').exists():
            raise PermissionDenied("Модераторы не могут создавать уроки")
        serializer.save(owner=self.request.user)


class LessonRetrieveView(generics.RetrieveAPIView):
    """Получение одного урока"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]


class LessonUpdateView(generics.UpdateAPIView):
    """Обновление урока"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrModerator]


class LessonDestroyView(generics.DestroyAPIView):
    """Удаление урока"""
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

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