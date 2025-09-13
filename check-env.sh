#!/bin/bash
# Скрипт для проверки .env файла

echo "🔍 Проверка .env файла..."

if [ ! -f ".env" ]; then
    echo "❌ Файл .env не найден!"
    echo "📋 Создайте файл .env на основе .env.example:"
    echo "   cp .env.example .env"
    echo "   # Затем отредактируйте .env под ваши настройки"
    exit 1
fi

echo "✅ Файл .env найден"

# Проверяем обязательные переменные
required_vars=("MONGODB_URI" "DATABASE_NAME" "FLASK_HOST" "FLASK_PORT")

for var in ""; do
    if ! grep -q "^=" .env; then
        echo "❌ Переменная  не найдена в .env файле"
        exit 1
    fi
done

echo "✅ Все обязательные переменные найдены в .env файле"
echo "📋 Содержимое .env файла:"
echo "---"
cat .env
echo "---"
