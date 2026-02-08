from rest_framework import serializers
from .models import Payment
from lms.serializers import CourseSerializer, LessonSerializer


class PaymentSerializer(serializers.ModelSerializer):
    """Сериализатор для платежей"""

    class Meta:
        model = Payment
        fields = '__all__'
        read_only_fields = ('payment_date',)


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Сериализатор для детального отображения платежа"""
    course = CourseSerializer(read_only=True)
    lesson = LessonSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = '__all__'