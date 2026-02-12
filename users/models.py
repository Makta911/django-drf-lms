from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Кастомный менеджер для модели User с email в качестве username"""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Кастомная модель пользователя"""
    username = None
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=15, blank=True, null=True)
    city = models.CharField(_('city'), max_length=100, blank=True, null=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email



class Payment(models.Model):
    """Модель платежа"""

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', _('Наличные')
        TRANSFER = 'transfer', _('Перевод на счет')


    user = models.ForeignKey(
        'User',
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name=_('пользователь')
    )
    payment_date = models.DateTimeField(_('дата оплаты'), auto_now_add=True)


    course = models.ForeignKey(
        'lms.Course',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('оплаченный курс')
    )
    lesson = models.ForeignKey(
        'lms.Lesson',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name=_('оплаченный урок')
    )
    amount = models.DecimalField(
        _('сумма оплаты'),
        max_digits=10,
        decimal_places=2
    )
    payment_method = models.CharField(
        _('способ оплаты'),
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.TRANSFER
    )

    class Meta:
        verbose_name = _('платеж')
        verbose_name_plural = _('платежи')
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.user.email} - {self.amount} руб. - {self.payment_date}"

    def clean(self):
        """Валидация: должен быть указан либо курс, либо урок"""
        from django.core.exceptions import ValidationError
        if self.course and self.lesson:
            raise ValidationError(_('Нельзя указать одновременно курс и урок'))
        if not self.course and not self.lesson:
            raise ValidationError(_('Должен быть указан либо курс, либо урок'))