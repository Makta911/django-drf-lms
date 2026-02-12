from rest_framework.pagination import PageNumberPagination


class CoursePagination(PageNumberPagination):
    """Пагинация для курсов"""
    page_size = 10  # Количество элементов на странице по умолчанию
    page_size_query_param = 'page_size'  # Параметр для изменения размера страницы
    max_page_size = 50  # Максимальный размер страницы


class LessonPagination(PageNumberPagination):
    """Пагинация для уроков"""
    page_size = 15
    page_size_query_param = 'page_size'
    max_page_size = 100


class SubscriptionPagination(PageNumberPagination):
    """Пагинация для подписок"""
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100