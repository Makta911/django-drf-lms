from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
import logging

User = get_user_model()
logger = logging.getLogger(__name__)


@shared_task
def check_inactive_users():
    """
    Проверка пользователей, которые не заходили более месяца
    и блокировка их аккаунтов
    """
    try:
        month_ago = timezone.now() - timedelta(days=30)

        inactive_users = User.objects.filter(
            last_login__lt=month_ago,
            is_active=True
        )

        user_count = inactive_users.count()

        if user_count == 0:
            logger.info("Неактивных пользователей не найдено")
            return "Неактивных пользователей не найдено"

        # Блокируем пользователей
        inactive_users.update(is_active=False)

        # Логируем
        emails = list(inactive_users.values_list('email', flat=True))
        logger.info(f"Заблокировано {user_count} неактивных пользователей: {emails}")

        # Отправляем отчет администраторам
        send_inactive_users_report.delay(user_count, emails)

        return f"Заблокировано {user_count} неактивных пользователей"

    except Exception as e:
        logger.error(f"Ошибка при проверке неактивных пользователей: {str(e)}")
        raise


@shared_task
def send_inactive_users_report(count, emails=None):
    """
    Отправка отчета администратору о заблокированных пользователях
    """
    try:
        subject = "Отчет о неактивных пользователях"

        email_list = "\n".join(emails) if emails else "Список недоступен"

        message = f"""
        Отчет о выполнении периодической задачи:

        Заблокировано неактивных пользователей: {count}

        Заблокированные пользователи:
        {email_list}

        Время выполнения: {timezone.now()}

        Это автоматическое сообщение от системы LMS.
        """

        # Получаем email администраторов
        admin_users = User.objects.filter(is_staff=True, is_active=True)
        admin_emails = [admin.email for admin in admin_users if admin.email]

        if admin_emails:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=True,
            )

        logger.info(f"Отчет отправлен {len(admin_emails)} администраторам")
        return f"Отчет отправлен {len(admin_emails)} администраторам"

    except Exception as e:
        logger.error(f"Ошибка при отправке отчета: {str(e)}")
        raise


@shared_task
def unblock_user_after_period(user_id, days=30):
    """
    Разблокировка пользователя через указанный период
    (дополнительная функция)
    """
    try:
        user = User.objects.get(id=user_id)

        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])

            logger.info(f"Пользователь {user.email} разблокирован")

            # Отправляем уведомление пользователю
            send_user_unblocked_notification.delay(user.email)

            return f"Пользователь {user.email} разблокирован"
        else:
            return f"Пользователь {user.email} уже активен"

    except User.DoesNotExist:
        return f"Пользователь с ID {user_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка при разблокировке пользователя: {str(e)}")
        raise


@shared_task
def send_user_unblocked_notification(email):
    """
    Отправка уведомления пользователю о разблокировке
    """
    try:
        subject = "Ваш аккаунт разблокирован"
        message = f"""
        Добрый день!

        Ваш аккаунт был автоматически разблокирован.

        Теперь вы можете снова войти в систему по адресу:
        {settings.FRONTEND_URL}/login/

        С уважением,
        Команда LMS платформы
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=True,
        )

        logger.info(f"Уведомление о разблокировке отправлено на {email}")
        return f"Уведомление отправлено на {email}"

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {str(e)}")
        raise


@shared_task
def send_welcome_email(user_id):
    """
    Отправка приветственного письма новому пользователю
    """
    try:
        user = User.objects.get(id=user_id)

        subject = f"Добро пожаловать в LMS, {user.first_name or 'пользователь'}!"

        message = f"""
        Добро пожаловать в нашу образовательную платформу!

        Ваш email для входа: {user.email}

        Теперь у вас есть доступ к:
        - Курсам и урокам
        - Личному кабинету
        - Прогрессу обучения

        Начните обучение прямо сейчас: {settings.FRONTEND_URL}

        С уважением,
        Команда LMS платформы
        """

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        logger.info(f"Приветственное письмо отправлено на {user.email}")
        return f"Приветственное письмо отправлено на {user.email}"

    except User.DoesNotExist:
        return f"Пользователь с ID {user_id} не найден"
    except Exception as e:
        logger.error(f"Ошибка при отправке приветственного письма: {str(e)}")
        raise


@shared_task
def test_user_task(message="Test from users app"):
    """Тестовая задача для проверки работы Celery"""
    logger.info(f"[{timezone.now()}] Users task: {message}")
    return f"Users task completed: {message}"