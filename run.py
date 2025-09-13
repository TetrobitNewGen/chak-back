#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для быстрого запуска приложения изучения татарского языка
"""

import subprocess
import sys
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

def check_mongodb():
    """Проверка запуска MongoDB"""
    try:
        import pymongo
        MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        client = pymongo.MongoClient(MONGODB_URI, serverSelectionTimeoutMS=2000)
        client.server_info()
        print(f"✅ MongoDB подключен успешно: {MONGODB_URI}")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к MongoDB: {e}")
        print("Убедитесь, что MongoDB запущен и проверьте настройки в .env файле")
        return False

def install_requirements():
    """Установка зависимостей"""
    print("📦 Установка зависимостей...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Зависимости установлены")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def init_database():
    """Инициализация базы данных"""
    print("��️ Инициализация базы данных...")
    try:
        subprocess.check_call([sys.executable, "init_db.py"])
        print("✅ База данных инициализирована")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        return False

def run_app():
    """Запуск приложения"""
    print("🚀 Запуск приложения...")
    try:
        subprocess.check_call([sys.executable, "app.py"])
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка запуска приложения: {e}")

def main():
    print("=== Запуск приложения изучения татарского языка ===\n")
    
    # Проверка .env файла
    if not os.path.exists('.env'):
        print("❌ Файл .env не найден! Создайте файл .env с настройками MongoDB")
        return
    
    # Проверка MongoDB
    if not check_mongodb():
        return
    
    # Установка зависимостей
    if not install_requirements():
        return
    
    # Инициализация базы данных
    if not init_database():
        return
    
    # Запуск приложения
    run_app()

if __name__ == "__main__":
    main()
