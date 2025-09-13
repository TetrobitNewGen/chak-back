#!/bin/bash
# Скрипт для локальной разработки

echo "🚀 Запуск приложения для разработки..."

# Проверка .env файла
if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "📋 Создайте файл .env на основе .env.example:"
    echo "   cp .env.example .env"
    echo "   # Затем отредактируйте .env под ваши настройки"
    exit 1
fi

echo "✅ Файл .env найден"

# Остановка существующих контейнеров
echo "🛑 Остановка существующих контейнеров..."
docker-compose down

# Сборка и запуск
echo "🔨 Сборка и запуск контейнеров..."
docker-compose up --build

echo "✅ Приложение запущено!"
echo "📱 API доступно по адресу: http://localhost:5000"
echo "📚 Swagger документация: http://localhost:5000/docs"
echo "🗄️ MongoDB доступна по адресу: localhost:27017"
