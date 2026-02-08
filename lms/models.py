from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()


class Course(models.Model):
    """Модель курса"""
    title = models.CharField(_('title'), max_length=255)
    preview = models.ImageField(_('preview'), upload_to='courses/previews/', blank=True, null=True)
    description = models.TextField(_('description'), blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name=_('владелец')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('course')
        verbose_name_plural = _('courses')
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """Модель урока"""
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='lessons',
        verbose_name=_('course')
    )
    title = models.CharField(_('title'), max_length=255)
    description = models.TextField(_('description'), blank=True)
    preview = models.ImageField(_('preview'), upload_to='lessons/previews/', blank=True, null=True)
    video_url = models.URLField(_('video URL'), blank=True)
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lessons',
        verbose_name=_('владелец')
    )
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)

    class Meta:
        verbose_name = _('lesson')
        verbose_name_plural = _('lessons')
        ordering = ['created_at']

    def __str__(self):
        return f"{self.title} ({self.course.title})"