# create_test_data.py
import os
import django
import random
from decimal import Decimal
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from lms.models import Course, Lesson
from users.models import Payment

User = get_user_model()

print("=== Создание тестовых данных ===")

# 1. Создаем пользователей
print("1. Создаем пользователей...")
if not User.objects.filter(email='admin@example.com').exists():
    admin = User.objects.create_superuser(
        email='admin@example.com',
        password='admin123',
        first_name='Админ',
        last_name='Админов',
        phone='+79990000000',
        city='Москва'
    )
    print(f"  Создан суперпользователь: {admin.email}")

if not User.objects.filter(email='user1@example.com').exists():
    user1 = User.objects.create_user(
        email='user1@example.com',
        password='user123',
        first_name='Иван',
        last_name='Иванов',
        phone='+79111234567',
        city='Москва'
    )
    print(f"  Создан пользователь: {user1.email}")

if not User.objects.filter(email='user2@example.com').exists():
    user2 = User.objects.create_user(
        email='user2@example.com',
        password='user123',
        first_name='Петр',
        last_name='Петров',
        phone='+79219876543',
        city='Санкт-Петербург'
    )
    print(f"  Создан пользователь: {user2.email}")

# 2. Создаем курсы
print("\n2. Создаем курсы...")
courses_data = [
    {
        'title': 'Python для начинающих',
        'description': 'Полный курс по основам Python для новичков'
    },
    {
        'title': 'Django Web Development',
        'description': 'Создание веб-приложений на Django'
    },
    {
        'title': 'JavaScript Advanced',
        'description': 'Продвинутый JavaScript и современные фреймворки'
    }
]

for course_data in courses_data:
    course, created = Course.objects.get_or_create(
        title=course_data['title'],
        defaults=course_data
    )
    if created:
        print(f"  Создан курс: {course.title}")

# 3. Создаем уроки
print("\n3. Создаем уроки...")
lessons_data = [
    {
        'course': Course.objects.get(title='Python для начинающих'),
        'title': 'Введение в Python',
        'description': 'Первое знакомство с языком Python',
        'video_url': 'https://example.com/python-intro'
    },
    {
        'course': Course.objects.get(title='Python для начинающих'),
        'title': 'Переменные и типы данных',
        'description': 'Работа с переменными и основными типами данных',
        'video_url': 'https://example.com/python-variables'
    },
    {
        'course': Course.objects.get(title='Python для начинающих'),
        'title': 'Функции в Python',
        'description': 'Создание и использование функций',
        'video_url': 'https://example.com/python-functions'
    },
    {
        'course': Course.objects.get(title='Django Web Development'),
        'title': 'Введение в Django',
        'description': 'Основы Django фреймворка',
        'video_url': 'https://example.com/django-intro'
    },
    {
        'course': Course.objects.get(title='Django Web Development'),
        'title': 'Модели Django',
        'description': 'Работа с моделями и базой данных',
        'video_url': 'https://example.com/django-models'
    },
    {
        'course': Course.objects.get(title='JavaScript Advanced'),
        'title': 'ES6+ Новые возможности',
        'description': 'Современный JavaScript: стрелочные функции, промисы',
        'video_url': 'https://example.com/js-es6'
    }
]

for lesson_data in lessons_data:
    lesson, created = Lesson.objects.get_or_create(
        course=lesson_data['course'],
        title=lesson_data['title'],
        defaults=lesson_data
    )
    if created:
        print(f"  Создан урок: {lesson.title} (курс: {lesson.course.title})")

# 4. Создаем платежи
print("\n4. Создаем платежи...")
Payment.objects.all().delete()  # Очищаем старые платежи

users = list(User.objects.all())
courses = list(Course.objects.all())
lessons = list(Lesson.objects.all())

payment_methods = ['cash', 'transfer']

for i in range(15):
    user = random.choice(users)
    is_course = random.choice([True, False])

    if is_course and courses:
        course = random.choice(courses)
        lesson = None
        amount = Decimal(str(round(random.uniform(1000, 5000), 2)))
    elif lessons:
        course = None
        lesson = random.choice(lessons)
        amount = Decimal(str(round(random.uniform(100, 1000), 2)))
    else:
        continue

    payment_method = random.choice(payment_methods)
    random_days = random.randint(0, 60)
    payment_date = timezone.now() - timedelta(days=random_days)

    payment = Payment.objects.create(
        user=user,
        course=course,
        lesson=lesson,
        amount=amount,
        payment_method=payment_method,
    )
    # Обновляем дату вручную
    payment.payment_date = payment_date
    payment.save()
    print(f"  Создан платеж #{i + 1}: {user.email} - {amount} руб. - {payment_method}")

print(f"\n=== ИТОГО ===")
print(f"Пользователей: {User.objects.count()}")
print(f"Курсов: {Course.objects.count()}")
print(f"Уроков: {Lesson.objects.count()}")
print(f"Платежей: {Payment.objects.count()}")
print("=================")