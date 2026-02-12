from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Создание тестовых платежей'

    def handle(self, *args, **kwargs):
        # Импортируем внутри функции чтобы избежать циклического импорта
        from django.contrib.auth import get_user_model
        from lms.models import Course, Lesson
        from users.models import Payment
        from decimal import Decimal
        import random
        from django.utils import timezone
        from datetime import timedelta

        User = get_user_model()

        # Создаем тестовые данные
        users = User.objects.all()
        courses = Course.objects.all()
        lessons = Lesson.objects.all()

        if not users.exists():
            self.stdout.write(self.style.ERROR('Нет пользователей. Сначала создайте пользователей.'))
            return

        if not courses.exists():
            self.stdout.write(self.style.ERROR('Нет курсов. Сначала создайте курсы.'))
            return

        if not lessons.exists():
            self.stdout.write(self.style.ERROR('Нет уроков. Сначала создайте уроки.'))
            return

        # Удаляем старые платежи
        Payment.objects.all().delete()

        payments = []

        for i in range(20):  # Создаем 20 платежей
            user = random.choice(users)
            is_course = random.choice([True, False])

            if is_course and courses.exists():
                course = random.choice(courses)
                lesson = None
                amount = Decimal(str(round(random.uniform(1000, 5000), 2)))
            elif lessons.exists():
                course = None
                lesson = random.choice(lessons)
                amount = Decimal(str(round(random.uniform(100, 1000), 2)))
            else:
                continue

            payment_method = random.choice(['cash', 'transfer'])

            # Случайная дата в пределах последних 30 дней
            random_days = random.randint(0, 30)
            payment_date = timezone.now() - timedelta(days=random_days)

            payment = Payment(
                user=user,
                course=course,
                lesson=lesson,
                amount=amount,
                payment_method=payment_method,
            )
            payment.payment_date = payment_date  # Переопределяем auto_now_add
            payments.append(payment)

        Payment.objects.bulk_create(payments)

        self.stdout.write(self.style.SUCCESS(f'Успешно создано {len(payments)} платежей'))