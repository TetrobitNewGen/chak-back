#!/bin/bash
# Скрипт для продакшена

echo "🚀 Запуск приложения в продакшене..."

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
docker-compose -f docker-compose.prod.yml down

# Сборка и запуск
echo "🔨 Сборка и запуск контейнеров..."
docker-compose -f docker-compose.prod.yml up --build -d

echo "✅ Приложение запущено в продакшене!"
echo "📱 API доступно по адресу: http://localhost:80"
echo "📚 Swagger документация: http://localhost:80/docs"
echo "🗄️ MongoDB доступна по адресу: localhost:27017"

# Показ логов
echo "📋 Логи приложения:"
docker-compose -f docker-compose.prod.yml logs -f app
