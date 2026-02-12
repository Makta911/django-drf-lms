from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import logging

from .models import Course, Subscription

# УДАЛИТЕ ЭТУ СТРОКУ: from user.models import User
# ВМЕСТО ЭТОГО используйте get_user_model() если нужно

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notification(course_id, update_message=None):
    """
    Отправка уведомлений об обновлении курса подписчикам
    """
    try:
        course = Course.objects.get(id=course_id)

        # Получаем всех подписчиков курса
        subscriptions = Subscription.objects.filter(course=course, is_active=True)

        if not subscriptions.exists():
            logger.info(f"У курса {course.title} нет активных подписчиков")
            return

        subject = f"Обновление курса: {course.title}"

        # Формируем сообщение
        if update_message:
            message = update_message
        else:
            message = f"""
            Добрый день!

            Курс "{course.title}" был обновлен.

            Новые материалы уже доступны в вашем личном кабинете.

            Ссылка на курс: {settings.FRONTEND_URL}/courses/{course.id}/

            С уважением,
            Команда LMS платформы
            """

        # Собираем email адреса подписчиков
        recipients = [sub.user.email for sub in subscriptions.select_related('user')]

        # Отправляем письма
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipients,
            fail_silently=False,
        )

        logger.info(f"Отправлены уведомления {len(recipients)} подписчикам курса {course.title}")

        # Обновляем время последнего уведомления
        course.last_notification_sent = timezone.now()
        course.save(update_fields=['last_notification_sent'])

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений: {str(e)}")
        raise


@shared_task
def send_course_updates_notifications():
    """
    Периодическая задача: проверка обновлений курсов за последние 4 часа
    и отправка уведомлений
    """
    four_hours_ago = timezone.now() - timedelta(hours=4)

    # Находим курсы, обновленные за последние 4 часа
    updated_courses = Course.objects.filter(
        updated_at__gte=four_hours_ago,
        updated_at__lte=timezone.now()
    )

    # Проверяем, что уведомление не отправлялось за последние 4 часа
    courses_to_notify = []
    for course in updated_courses:
        if not course.last_notification_sent or \
                course.last_notification_sent < four_hours_ago:
            courses_to_notify.append(course.id)

    # Отправляем уведомления для каждого курса
    for course_id in courses_to_notify:
        send_course_update_notification.delay(course_id)

    logger.info(f"Проверка обновлений завершена. Найдено курсов для уведомления: {len(courses_to_notify)}")
    return f"Отправлено уведомлений для {len(courses_to_notify)} курсов"


@shared_task
def check_specific_lesson_update(course_id, lesson_title):
    """
    Проверка обновления конкретного урока
    (Дополнительное задание)
    """
    try:
        course = Course.objects.get(id=course_id)
        four_hours_ago = timezone.now() - timedelta(hours=4)

        # Проверяем, были ли обновления уроков за последние 4 часа
        recent_lessons = course.lessons.filter(
            updated_at__gte=four_hours_ago,
            title__icontains=lesson_title
        )

        if recent_lessons.exists() and (
                not course.last_notification_sent or
                course.last_notification_sent < four_hours_ago
        ):
            message = f"""
            Добрый день!

            В курсе "{course.title}" был обновлен урок "{lesson_title}".

            Новые материалы уже доступны в вашем личном кабинете.

            Ссылка на курс: {settings.FRONTEND_URL}/courses/{course.id}/

            С уважением,
            Команда LMS платформы
            """

            send_course_update_notification.delay(course_id, message)
            return f"Уведомление отправлено об обновлении урока {lesson_title}"

        return "Обновлений не обнаружено или уведомление уже отправлялось"

    except Course.DoesNotExist:
        return f"Курс с ID {course_id} не найден"