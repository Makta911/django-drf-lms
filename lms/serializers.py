from rest_framework import serializers
from .models import Course, Lesson
# НЕ импортируйте Subscription здесь, импортируйте внутри класса если нужно
from .validators import YouTubeURLValidator, validate_youtube_url


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для урока"""

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'owner')
        # Используем валидатор (можно использовать класс или функцию)
        validators = [
            YouTubeURLValidator(field='video_url'),
        ]

    # Или можно использовать валидатор для конкретного поля
    video_url = serializers.URLField(
        required=False,
        allow_blank=True,
        validators=[validate_youtube_url]  # Функция-валидатор
    )

    def create(self, validated_data):
        """Автоматически устанавливаем владельца при создании"""
        user = self.context['request'].user
        validated_data['owner'] = user
        return super().create(validated_data)


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курса"""
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'owner')

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяем подписан ли текущий пользователь на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Импортируем здесь чтобы избежать циклического импорта
            from .models import Subscription
            # Проверяем активную подписку
            return obj.subscriptions.filter(
                user=request.user,
                is_active=True
            ).exists()
        return False

    def create(self, validated_data):
        """Автоматически устанавливаем владельца при создании"""
        user = self.context['request'].user
        validated_data['owner'] = user
        return super().create(validated_data)


class SubscriptionSerializer(serializers.ModelSerializer):
    """Сериализатор для подписки"""

    class Meta:
        # Импортируем модель внутри класса
        from .models import Subscription
        model = Subscription
        fields = ['id', 'user', 'course', 'is_active', 'subscribed_at', 'updated_at']
        read_only_fields = ['user', 'subscribed_at', 'updated_at']

    def validate(self, data):
        """Валидация подписки"""
        request = self.context.get('request')
        course = data.get('course')

        # Импортируем модель
        from .models import Subscription

        # Проверяем что пользователь не подписан уже
        if request and request.user.is_authenticated:
            existing_subscription = Subscription.objects.filter(
                user=request.user,
                course=course,
                is_active=True
            ).exists()

            if existing_subscription and self.instance is None:
                raise serializers.ValidationError(
                    'Вы уже подписаны на этот курс'
                )

        return data

    def create(self, validated_data):
        """При создании подписки устанавливаем текущего пользователя"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            validated_data['user'] = request.user
        return super().create(validated_data)