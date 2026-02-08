from rest_framework import serializers
from lms.models import Course, StripeProduct


class CoursePaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для оплаты курса"""

    class Meta:
        model = Course
        fields = ['id', 'title', 'description']


class StripeCheckoutSerializer(serializers.Serializer):
    """Сериализатор для создания сессии оплаты в Stripe"""
    course_id = serializers.IntegerField(required=True)
    success_url = serializers.URLField(
        required=False,
        default='http://localhost:3000/payment/success/'
    )
    cancel_url = serializers.URLField(
        required=False,
        default='http://localhost:3000/payment/cancel/'
    )

    def validate_course_id(self, value):
        """Проверяем что курс существует"""
        try:
            Course.objects.get(id=value)
        except Course.DoesNotExist:
            raise serializers.ValidationError("Курс не найден")
        return value