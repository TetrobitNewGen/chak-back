# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Обновляем pip
RUN pip install --upgrade pip

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код (исключая .env)
COPY . .

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Открываем порт
EXPOSE 5000

# Переменные окружения по умолчанию (будут переопределены .env файлом)
ENV MONGODB_URI=mongodb://mongo:27017/
ENV DATABASE_NAME=tatar_learning
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000
ENV FLASK_ENV=production
ENV FLASK_DEBUG=False

# Команда запуска
CMD ["python", "app.py"]
