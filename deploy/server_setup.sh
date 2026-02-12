#!/bin/bash

# Скрипт настройки удаленного сервера для деплоя Django приложения

set -e  # Прерывать выполнение при ошибке

echo "🚀 Начинаем настройку сервера..."

# Обновление системы
echo "📦 Обновление пакетов..."
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
echo "📦 Установка Python, Nginx, Redis, и других зависимостей..."
sudo apt install -y \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    nginx \
    redis-server \
    postgresql \
    postgresql-contrib \
    libpq-dev \
    git \
    curl \
    supervisor \
    certbot \
    python3-certbot-nginx \
    ufw

# Создание пользователя для приложения
echo "👤 Создание пользователя lms..."
sudo useradd -m -s /bin/bash lms || true
sudo usermod -aG sudo lms

# Настройка PostgreSQL
echo "🐘 Настройка PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание базы данных и пользователя
sudo -u postgres psql -c "CREATE DATABASE lms_db;" || true
sudo -u postgres psql -c "CREATE USER lms_user WITH PASSWORD 'your_strong_password_here';" || true
sudo -u postgres psql -c "ALTER ROLE lms_user SET client_encoding TO 'utf8';" || true
sudo -u postgres psql -c "ALTER ROLE lms_user SET default_transaction_isolation TO 'read committed';" || true
sudo -u postgres psql -c "ALTER ROLE lms_user SET timezone TO 'UTC';" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE lms_db TO lms_user;" || true

# Настройка Redis
echo "🔥 Настройка Redis..."
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Настройка Nginx
echo "🌐 Настройка Nginx..."
sudo rm -f /etc/nginx/sites-enabled/default
sudo tee /etc/nginx/sites-available/lms << EOF
server {
    listen 80;
    server_name _;  # Замените на ваш домен или IP

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /home/lms/app/staticfiles/;
    }

    location /media/ {
        alias /home/lms/app/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/lms/app/app.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/lms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Настройка Supervisor для управления Gunicorn
echo "🔄 Настройка Supervisor..."
sudo tee /etc/supervisor/conf.d/lms.conf << EOF
[program:lms]
command=/home/lms/venv/bin/gunicorn --workers 3 --bind unix:/home/lms/app/app.sock config.wsgi:application
directory=/home/lms/app
user=lms
autostart=true
autorestart=true
stopasgroup=true
killasgroup=true
stderr_logfile=/var/log/lms/lms.err.log
stdout_logfile=/var/log/lms/lms.out.log
environment=
    SECRET_KEY="django-insecure-production-key-change-this",
    DEBUG="False",
    DB_NAME="lms_db",
    DB_USER="lms_user",
    DB_PASSWORD="your_strong_password_here",
    DB_HOST="localhost",
    DB_PORT="5432",
    REDIS_HOST="localhost",
    REDIS_PORT="6379",
    REDIS_DB="0",
    DJANGO_SETTINGS_MODULE="config.settings",
    CELERY_BROKER_URL="redis://localhost:6379/0",
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
EOF

sudo mkdir -p /var/log/lms
sudo chown -R lms:lms /var/log/lms

# Настройка Supervisor для Celery Worker
sudo tee /etc/supervisor/conf.d/celery_worker.conf << EOF
[program:celery_worker]
command=/home/lms/venv/bin/celery -A config worker --loglevel=info
directory=/home/lms/app
user=lms
numprocs=1
stdout_logfile=/var/log/lms/celery_worker.log
stderr_logfile=/var/log/lms/celery_worker.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=60
environment=
    DJANGO_SETTINGS_MODULE="config.settings",
    SECRET_KEY="django-insecure-production-key-change-this",
    DEBUG="False",
    DB_NAME="lms_db",
    DB_USER="lms_user",
    DB_PASSWORD="your_strong_password_here",
    DB_HOST="localhost",
    DB_PORT="5432",
    REDIS_HOST="localhost",
    REDIS_PORT="6379",
    REDIS_DB="0",
    CELERY_BROKER_URL="redis://localhost:6379/0",
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
EOF

# Настройка Supervisor для Celery Beat
sudo tee /etc/supervisor/conf.d/celery_beat.conf << EOF
[program:celery_beat]
command=/home/lms/venv/bin/celery -A config beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
directory=/home/lms/app
user=lms
numprocs=1
stdout_logfile=/var/log/lms/celery_beat.log
stderr_logfile=/var/log/lms/celery_beat.log
autostart=true
autorestart=true
startsecs=10
stopwaitsecs=60
environment=
    DJANGO_SETTINGS_MODULE="config.settings",
    SECRET_KEY="django-insecure-production-key-change-this",
    DEBUG="False",
    DB_NAME="lms_db",
    DB_USER="lms_user",
    DB_PASSWORD="your_strong_password_here",
    DB_HOST="localhost",
    DB_PORT="5432",
    REDIS_HOST="localhost",
    REDIS_PORT="6379",
    REDIS_DB="0",
    CELERY_BROKER_URL="redis://localhost:6379/0",
    CELERY_RESULT_BACKEND="redis://localhost:6379/0"
EOF

# Настройка брандмауэра
echo "🛡️ Настройка брандмауэра..."
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw --force enable

# Создание директории для деплоя
sudo mkdir -p /home/lms/app
sudo chown -R lms:lms /home/lms

echo "✅ Настройка сервера завершена!"
echo "📝 Не забудьте:"
echo "  1. Заменить пароли в скрипте на реальные"
echo "  2. Настроить домен и SSL сертификат"
echo "  3. Добавить SSH ключи для пользователя lms"