from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta

from .models import Course, Lesson
from .tasks import send_course_update_notification


@receiver(post_save, sender=Course)
def course_updated_handler(sender, instance, created, **kwargs):
    """
    Отправка уведомлений при обновлении курса
    """
    if not created:  # Только при обновлении, не при создании
        four_hours_ago = timezone.now() - timedelta(hours=4)

        # Проверяем, что уведомление не отправлялось за последние 4 часа
        if not instance.last_notification_sent or \
                instance.last_notification_sent < four_hours_ago:
            # Запускаем асинхронную задачу
            send_course_update_notification.delay(instance.id)


@receiver(post_save, sender=Lesson)
def lesson_updated_handler(sender, instance, created, **kwargs):
    """
    Отправка уведомлений при обновлении урока
    (Дополнительное задание)
    """
    if not created and instance.course:
        four_hours_ago = timezone.now() - timedelta(hours=4)
        course = instance.course

        # Проверяем, что уведомление не отправлялось за последние 4 часа
        if not course.last_notification_sent or \
                course.last_notification_sent < four_hours_ago:
            message = f"""
            Добрый день!

            В курсе "{course.title}" был обновлен урок "{instance.title}".

            Новые материалы уже доступны в вашем личном кабинете.

            Ссылка на курс: {settings.FRONTEND_URL}/courses/{course.id}/

            С уважением,
            Команда LMS платформы
            """

            send_course_update_notification.delay(course.id, message)