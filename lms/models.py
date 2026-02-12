from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.conf import settings

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

    # ДОБАВЬТЕ ЭТО ПОЛЕ для отслеживания уведомлений
    last_notification_sent = models.DateTimeField(
        _('последнее уведомление отправлено'),
        null=True,
        blank=True
    )

    # ДОБАВЬТЕ ПОЛЕ ЦЕНЫ для оплаты
    price = models.DecimalField(
        _('цена'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )

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


class Subscription(models.Model):
    """Модель подписки на обновления курса"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('пользователь')
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('курс')
    )
    is_active = models.BooleanField(_('активна'), default=True)
    subscribed_at = models.DateTimeField(_('дата подписки'), auto_now_add=True)
    updated_at = models.DateTimeField(_('дата обновления'), auto_now=True)

    class Meta:
        verbose_name = _('подписка')
        verbose_name_plural = _('подписки')
        unique_together = ['user', 'course']  # Одна подписка на курс для пользователя
        ordering = ['-subscribed_at']

    def __str__(self):
        status = "активна" if self.is_active else "неактивна"
        return f"{self.user.email} -> {self.course.title} ({status})"


class StripeProduct(models.Model):
    """Модель для хранения информации о продуктах в Stripe"""
    course = models.OneToOneField(
        Course,
        on_delete=models.CASCADE,
        related_name='stripe_product',
        verbose_name=_('курс')
    )
    product_id = models.CharField(
        _('ID продукта в Stripe'),
        max_length=100,
        unique=True
    )
    price_id = models.CharField(
        _('ID цены в Stripe'),
        max_length=100,
        unique=True
    )
    created_at = models.DateTimeField(_('создан'), auto_now_add=True)
    updated_at = models.DateTimeField(_('обновлен'), auto_now=True)

    class Meta:
        verbose_name = _('продукт Stripe')
        verbose_name_plural = _('продукты Stripe')

    def __str__(self):
        return f"{self.course.title} - {self.product_id}"


class Payment:
    pass