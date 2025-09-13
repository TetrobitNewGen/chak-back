#!/bin/bash
# Скрипт для локальной разработки

echo "🚀 Запуск приложения для разработки..."

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
