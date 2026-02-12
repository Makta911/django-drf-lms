from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from .views import (
    UserRegistrationAPIView,
    UserListAPIView,
    UserDetailAPIView,
    UserProfileAPIView,
    CustomTokenObtainPairView,
    PaymentListAPIView,
    PaymentRetrieveAPIView,
)

urlpatterns = [
    # Аутентификация (доступно всем)
    path('register/', UserRegistrationAPIView.as_view(), name='user-register'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token-verify'),

    # Пользователи (требуется авторизация)
    path('', UserListAPIView.as_view(), name='user-list'),
    path('profile/', UserProfileAPIView.as_view(), name='user-profile'),
    path('<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),

    # Платежи
    path('payments/', PaymentListAPIView.as_view(), name='payment-list'),
    path('payments/<int:pk>/', PaymentRetrieveAPIView.as_view(), name='payment-detail'),
]