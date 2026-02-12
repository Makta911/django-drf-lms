#!/bin/bash

# Скрипт автоматического деплоя на удаленный сервер

set -e

echo "🚀 Начинаем деплой приложения..."

SERVER_USER=${SERVER_USER:-lms}
SERVER_HOST=${SERVER_HOST:-your-server-ip}
SERVER_PATH=${SERVER_PATH:-/home/lms/app}

# Создание временной директории
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
TEMP_DIR="/tmp/lms_deploy_$TIMESTAMP"

echo "📦 Подготовка файлов для деплоя..."
mkdir -p $TEMP_DIR

# Копирование файлов проекта
cp -r \
    config \
    users \
    lms \
    payments \
    manage.py \
    requirements.txt \
    .env.production \
    $TEMP_DIR/

# Создание .env файла из шаблона
cp .env.production $TEMP_DIR/.env

# Архивирование проекта
cd /tmp
tar -czf "lms_$TIMESTAMP.tar.gz" "lms_deploy_$TIMESTAMP"

echo "📤 Отправка файлов на сервер..."
scp -o StrictHostKeyChecking=no \
    "/tmp/lms_$TIMESTAMP.tar.gz" \
    "$SERVER_USER@$SERVER_HOST:/tmp/"

# Выполнение команд на сервере
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_HOST" << EOF
    set -e

    echo "📂 Распаковка файлов..."
    sudo mkdir -p $SERVER_PATH
    sudo tar -xzf "/tmp/lms_$TIMESTAMP.tar.gz" -C $SERVER_PATH --strip-components=1
    sudo chown -R $SERVER_USER:$SERVER_USER $SERVER_PATH

    echo "🐍 Настройка виртуального окружения..."
    cd $SERVER_PATH

    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
    fi
    source venv/bin/activate

    echo "📦 Установка зависимостей..."
    pip install --upgrade pip
    pip install -r requirements.txt

    echo "⚙️ Применение миграций..."
    python manage.py migrate --noinput

    echo "📊 Сбор статических файлов..."
    python manage.py collectstatic --noinput

    echo "🔄 Перезапуск сервисов..."
    sudo supervisorctl reread
    sudo supervisorctl update
    sudo supervisorctl restart lms
    sudo supervisorctl restart celery_worker
    sudo supervisorctl restart celery_beat

    echo "🧹 Очистка временных файлов..."
    rm "/tmp/lms_$TIMESTAMP.tar.gz"

    echo "✅ Деплой завершен успешно!"
EOF

# Очистка локальных временных файлов
rm -rf "$TEMP_DIR"
rm "/tmp/lms_$TIMESTAMP.tar.gz"

echo "🎉 Деплой на $SERVER_HOST завершен!"