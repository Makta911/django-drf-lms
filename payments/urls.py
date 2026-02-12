from django.urls import path
from .views import (
    StripeCheckoutAPIView,
    StripeWebhookAPIView,
    CoursePriceAPIView,
)

urlpatterns = [
    path('checkout/', StripeCheckoutAPIView.as_view(), name='stripe-checkout'),
    path('webhook/', StripeWebhookAPIView.as_view(), name='stripe-webhook'),
    path('courses/<int:pk>/price/', CoursePriceAPIView.as_view(), name='course-price'),
]