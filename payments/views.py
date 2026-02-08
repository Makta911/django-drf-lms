import stripe
from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import StripeCheckoutSerializer, CoursePaymentSerializer
from lms.models import Course, StripeProduct, Payment

# Настройка Stripe
stripe.api_key = settings.STRIPE_API_KEY


class StripeCheckoutAPIView(APIView):
    """
    API для создания сессии оплаты в Stripe.

    Создает или получает продукт в Stripe, создает цену и сессию оплаты.
    Возвращает URL для перенаправления пользователя на страницу оплаты Stripe.
    """
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Создать сессию оплаты для курса в Stripe",
        request_body=StripeCheckoutSerializer,
        responses={
            200: openapi.Response(
                description="Сессия создана",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'checkout_url': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='URL для перенаправления на страницу оплаты Stripe'
                        ),
                        'session_id': openapi.Schema(
                            type=openapi.TYPE_STRING,
                            description='ID сессии в Stripe'
                        )
                    }
                )
            ),
            400: "Неверные данные",
            404: "Курс не найден",
            500: "Ошибка Stripe API"
        }
    )
    def post(self, request):
        serializer = StripeCheckoutSerializer(data=request.data)
        if serializer.is_valid():
            course_id = serializer.validated_data['course_id']
            success_url = serializer.validated_data['success_url']
            cancel_url = serializer.validated_data['cancel_url']

            try:
                course = Course.objects.get(id=course_id)

                # Проверяем существует ли уже продукт в Stripe
                stripe_product = self.get_or_create_stripe_product(course)

                # Создаем сессию checkout в Stripe
                checkout_session = stripe.checkout.Session.create(
                    payment_method_types=['card'],
                    line_items=[{
                        'price': stripe_product.price_id,
                        'quantity': 1,
                    }],
                    mode='payment',
                    success_url=success_url,
                    cancel_url=cancel_url,
                    metadata={
                        'course_id': str(course.id),
                        'user_id': str(request.user.id),
                        'course_title': course.title
                    },
                    customer_email=request.user.email,
                )

                # Создаем запись о платеже (ожидающий оплаты)
                Payment.objects.create(
                    user=request.user,
                    course=course,
                    amount=5000,  # Фиксированная цена для примера
                    payment_method='transfer',  # Для Stripe
                )

                return Response({
                    'checkout_url': checkout_session.url,
                    'session_id': checkout_session.id
                }, status=status.HTTP_200_OK)

            except Course.DoesNotExist:
                return Response(
                    {'error': 'Курс не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
            except stripe.error.StripeError as e:
                return Response(
                    {'error': f'Ошибка Stripe: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            except Exception as e:
                return Response(
                    {'error': f'Ошибка сервера: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get_or_create_stripe_product(self, course):
        """Создает или получает продукт в Stripe"""
        try:
            # Пытаемся найти существующий продукт
            stripe_product = StripeProduct.objects.get(course=course)
            return stripe_product
        except StripeProduct.DoesNotExist:
            # Создаем новый продукт в Stripe
            product = stripe.Product.create(
                name=course.title,
                description=course.description or "Онлайн курс",
                metadata={
                    'course_id': str(course.id),
                    'type': 'course'
                }
            )

            # Создаем цену для продукта
            price = stripe.Price.create(
                unit_amount=5000,  # 50.00 USD в центах
                currency='usd',
                recurring=None,  # Разовый платеж
                product=product.id,
                metadata={
                    'course_id': str(course.id)
                }
            )

            # Сохраняем в базе данных
            stripe_product = StripeProduct.objects.create(
                course=course,
                product_id=product.id,
                price_id=price.id
            )

            return stripe_product


class StripeWebhookAPIView(APIView):
    """
    Webhook для обработки событий от Stripe.

    Обрабатывает успешные оплаты и обновляет статусы платежей.
    Не требует аутентификации (вызывается Stripe).
    """
    permission_classes = []  # No authentication required for webhooks

    @swagger_auto_schema(
        operation_description="Webhook для обработки событий Stripe",
        request_body=openapi.Schema(
            type=openapi.TYPE_STRING,
            description='Raw event data from Stripe'
        ),
        responses={
            200: "Webhook обработан",
            400: "Неверная подпись webhook",
            500: "Ошибка обработки webhook"
        }
    )
    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError as e:
            # Invalid payload
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Invalid signature
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Обработка событий
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            self.handle_checkout_session_completed(session)

        elif event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            self.handle_payment_intent_succeeded(payment_intent)

        return Response({'status': 'success'}, status=status.HTTP_200_OK)

    def handle_checkout_session_completed(self, session):
        """Обработка успешного завершения сессии оплаты"""
        try:
            course_id = session['metadata']['course_id']
            user_id = session['metadata']['user_id']

            # Обновляем статус платежа
            payment = Payment.objects.filter(
                user_id=user_id,
                course_id=course_id,
                payment_method='transfer'
            ).last()

            if payment:
                payment.payment_method = 'stripe'
                # Можно добавить дополнительные поля: transaction_id и т.д.
                payment.save()

        except (KeyError, Payment.DoesNotExist):
            pass

    def handle_payment_intent_succeeded(self, payment_intent):
        """Обработка успешного платежа"""
        # Можно добавить дополнительную логику обработки
        pass


class CoursePriceAPIView(generics.RetrieveAPIView):
    """
    API для получения информации о цене курса.
    """
    queryset = Course.objects.all()
    serializer_class = CoursePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Получить информацию о курсе для оплаты",
        responses={
            200: CoursePaymentSerializer,
            404: "Курс не найден"
        }
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)