from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CourseViewSet,
    LessonListCreateView,
    LessonRetrieveView,
    LessonUpdateView,
    LessonDestroyView,
    SubscriptionViewSet,
)

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'subscriptions', SubscriptionViewSet, basename='subscription')

urlpatterns = [
    path('', include(router.urls)),

    # URL для уроков
    path('lessons/', LessonListCreateView.as_view(), name='lesson-list'),
    path('lessons/<int:pk>/', LessonRetrieveView.as_view(), name='lesson-detail'),
    path('lessons/<int:pk>/update/', LessonUpdateView.as_view(), name='lesson-update'),
    path('lessons/<int:pk>/delete/', LessonDestroyView.as_view(), name='lesson-delete'),

    # Эндпоинты для подписок
    path('subscriptions/subscribe/', SubscriptionViewSet.as_view({'post': 'subscribe'}), name='subscription-subscribe'),
    path('subscriptions/unsubscribe/', SubscriptionViewSet.as_view({'post': 'unsubscribe'}),
         name='subscription-unsubscribe'),
]