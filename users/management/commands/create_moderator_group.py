from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Создание группы модераторов с ограниченными правами'

    def handle(self, *args, **kwargs):
        from lms.models import Course, Lesson


        moderator_group, created = Group.objects.get_or_create(name='moderators')

        if created:
            self.stdout.write(self.style.SUCCESS('Группа "moderators" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "moderators" уже существует'))

        # Получаем разрешения для моделей
        course_content_type = ContentType.objects.get_for_model(Course)
        lesson_content_type = ContentType.objects.get_for_model(Lesson)

        # Разрешения для курсов (без создания и удаления)
        course_permissions = Permission.objects.filter(
            content_type=course_content_type,
            codename__in=['view_course', 'change_course']
        )

        # Разрешения для уроков (без создания и удаления)
        lesson_permissions = Permission.objects.filter(
            content_type=lesson_content_type,
            codename__in=['view_lesson', 'change_lesson']
        )

        # Добавляем разрешения группе
        moderator_group.permissions.add(*course_permissions)
        moderator_group.permissions.add(*lesson_permissions)

        # Сохраняем
        moderator_group.save()

        self.stdout.write(self.style.SUCCESS(
            f'Группе "moderators" добавлены разрешения: {moderator_group.permissions.count()}'
        ))

        # Выводим список разрешений
        self.stdout.write('\nРазрешения модераторов:')
        for perm in moderator_group.permissions.all():
            self.stdout.write(f'  - {perm.name}')