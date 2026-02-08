from rest_framework import generics, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Payment
from .serializers import PaymentSerializer, PaymentDetailSerializer


class PaymentListAPIView(generics.ListAPIView):
    """Представление для списка платежей с фильтрацией"""
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['course', 'lesson', 'payment_method']
    ordering_fields = ['payment_date']
    ordering = ['-payment_date']  # по умолчанию сортировка по дате (новые первые)


class PaymentRetrieveAPIView(generics.RetrieveAPIView):
    """Представление для детального просмотра платежа"""
    queryset = Payment.objects.all()
    serializer_class = PaymentDetailSerializer