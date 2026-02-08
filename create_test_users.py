import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

User = get_user_model()

# Создаем суперпользователя
admin, created = User.objects.get_or_create(
    email='admin@example.com',
    defaults={
        'first_name': 'Admin',
        'last_name': 'User',
        'is_staff': True,
        'is_superuser': True
    }
)
if created:
    admin.set_password('admin123')
    admin.save()
    print(f"Создан суперпользователь: {admin.email}")

# Создаем обычного пользователя
user1, created = User.objects.get_or_create(
    email='user1@example.com',
    defaults={
        'first_name': 'Иван',
        'last_name': 'Иванов',
        'phone': '+79111234567',
        'city': 'Москва'
    }
)
if created:
    user1.set_password('user123')
    user1.save()
    print(f"Создан пользователь: {user1.email}")

# Создаем модератора
moderator, created = User.objects.get_or_create(
    email='moderator@example.com',
    defaults={
        'first_name': 'Петр',
        'last_name': 'Петров',
        'phone': '+79219876543',
        'city': 'Санкт-Петербург'
    }
)
if created:
    moderator.set_password('mod123')
    moderator.save()

    # Добавляем в группу модераторов
    moderators_group, _ = Group.objects.get_or_create(name='moderators')
    moderator.groups.add(moderators_group)
    moderator.save()
    print(f"Создан модератор: {moderator.email}")

print("Тестовые пользователи созданы!")