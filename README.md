# Django DRF LMS - Платформа онлайн-обучения

## 📋 Описание проекта

Платформа для онлайн-обучения с курсами, уроками, платежами через Stripe и асинхронными уведомлениями через Celery.

## 🚀 Технологический стек

- **Backend**: Django 4.2, Django REST Framework
- **Database**: PostgreSQL 15
- **Cache/Broker**: Redis 7
- **Async Tasks**: Celery 5.3, Celery Beat
- **Payments**: Stripe API
- **Containerization**: Docker, Docker Compose
- **Authentication**: JWT

## 📦 Установка и запуск через Docker Compose

### Предварительные требования

- Установленные [Docker](https://docs.docker.com/get-docker/) и [Docker Compose](https://docs.docker.com/compose/install/)
- Git

### Шаг 1: Клонирование репозитория

```bash
git clone https://github.com/Makta911/django-drf-lms.git
cd django-drf-lms