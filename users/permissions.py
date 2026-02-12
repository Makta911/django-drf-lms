from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Разрешение на доступ только владельцу или администратору"""

    def has_object_permission(self, request, view, obj):
        # Админы имеют полный доступ
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Владелец имеет доступ к своему объекту
        return obj == request.user


class IsModerator(permissions.BasePermission):
    """Проверка, является ли пользователь модератором"""

    def has_permission(self, request, view):
        return request.user.groups.filter(name='moderators').exists()

    def has_object_permission(self, request, view, obj):
        return request.user.groups.filter(name='moderators').exists()


class IsOwnerOrModerator(permissions.BasePermission):
    """Разрешение на доступ владельцу или модератору"""

    def has_object_permission(self, request, view, obj):
        # Админы имеют полный доступ
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Проверяем, есть ли у объекта поле 'owner'
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.groups.filter(name='moderators').exists()

        # Для пользователей сравниваем объект с request.user
        if hasattr(obj, 'email'):
            return obj == request.user or request.user.groups.filter(name='moderators').exists()

        # Для платежей проверяем user
        if hasattr(obj, 'user'):
            return obj.user == request.user or request.user.groups.filter(name='moderators').exists()

        return False


class IsOwner(permissions.BasePermission):
    """Разрешение на доступ только владельцу"""

    def has_object_permission(self, request, view, obj):
        # Админы имеют полный доступ
        if request.user.is_staff or request.user.is_superuser:
            return True

        # Проверяем, есть ли у объекта поле 'owner'
        if hasattr(obj, 'owner'):
            return obj.owner == request.user

        # Для пользователей сравниваем объект с request.user
        if hasattr(obj, 'email'):
            return obj == request.user

        # Для платежей проверяем user
        if hasattr(obj, 'user'):
            return obj.user == request.user

        return False