from rest_framework import serializers
from urllib.parse import urlparse


class YouTubeURLValidator:
    """
    Валидатор для проверки что ссылка ведет на youtube.com
    """

    def __init__(self, field='video_url'):
        self.field = field

    def __call__(self, attrs):
        # Получаем значение поля из attrs
        if self.field in attrs:
            value = attrs[self.field]
            if value:  # Проверяем только если значение не пустое
                parsed_url = urlparse(value)

                # Проверяем домен
                allowed_domains = ['youtube.com', 'www.youtube.com', 'youtu.be']
                domain = parsed_url.netloc.lower()

                # Проверяем вхождения разрешенных доменов
                if not any(allowed_domain in domain for allowed_domain in allowed_domains):
                    raise serializers.ValidationError({
                        self.field: 'Разрешены только ссылки на YouTube (youtube.com или youtu.be)'
                    })
        return attrs


def validate_youtube_url(value):
    """
    Функция-валидатор для проверки YouTube ссылок
    """
    if not value:
        return value

    parsed_url = urlparse(value)
    allowed_domains = ['youtube.com', 'www.youtube.com', 'youtu.be']
    domain = parsed_url.netloc.lower()

    # Проверяем домен
    is_valid = any(allowed_domain in domain for allowed_domain in allowed_domains)

    if not is_valid:
        raise serializers.ValidationError(
            'Разрешены только ссылки на YouTube. '
            'Используйте youtube.com или youtu.be'
        )

    return value