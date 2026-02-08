import os
from celery import Celery
from celery.schedules import crontab

# Устанавливаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('lms')

# Загружаем настройки из Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматическое обнаружение задач в приложениях
app.autodiscover_tasks()

# Конфигурация beat schedule
app.conf.beat_schedule = {
    'check-inactive-users-daily': {
        'task': 'user.tasks.check_inactive_users',
        'schedule': crontab(hour=0, minute=0),  # Ежедневно в полночь
        'args': (),
    },
    'send-course-updates-hourly': {
        'task': 'lms.tasks.send_course_updates_notifications',
        'schedule': crontab(hour='*/1', minute=0),  # Каждый час
        'args': (),
    },
}

app.conf.timezone = 'Europe/Moscow'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')