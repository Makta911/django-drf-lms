from rest_framework import serializers
from .models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
    """Сериализатор для урока"""

    class Meta:
        model = Lesson
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'owner')

    def create(self, validated_data):
        """Автоматически устанавливаем владельца при создании"""
        user = self.context['request'].user
        validated_data['owner'] = user
        return super().create(validated_data)


class CourseSerializer(serializers.ModelSerializer):
    """Сериализатор для курса"""
    lessons_count = serializers.SerializerMethodField()
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'owner')

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def create(self, validated_data):
        """Автоматически устанавливаем владельца при создании"""
        user = self.context['request'].user
        validated_data['owner'] = user
        return super().create(validated_data)