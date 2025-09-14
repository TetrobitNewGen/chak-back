#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для добавления слов из JSON файлов в папке words в MongoDB
"""

import json
from pymongo import MongoClient
import os
import glob
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

def add_words_from_json():
    """Добавление слов из JSON файлов в папке words в MongoDB"""
    
    # Получение конфигурации из .env
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'tatar_learning')
    
    try:
        # Подключение к MongoDB
        client = MongoClient(MONGODB_URI)
        db = client[DATABASE_NAME]
        words_collection = db['words']
        
        # Получение списка всех JSON файлов в папке words
        json_files = glob.glob('words/*.json')
        
        if not json_files:
            print('❌ В папке words не найдено JSON файлов')
            return False
        
        all_documents = []
        
        # Обработка каждого JSON файла
        for json_file in json_files:
            print(f'📖 Обработка файла: {json_file}')
            
            try:
                # Чтение JSON-файла
                with open(json_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)
                
                # Подготовка данных для вставки
                for word, definitions in data.items():
                    all_documents.append({
                        'word': word,
                        'definitions': definitions,
                        'difficulty': determine_difficulty(definitions),
                        'source_file': os.path.basename(json_file)  # Сохраняем имя файла-источника
                    })
                
                print(f'✅ Файл {json_file} обработан успешно')
                
            except Exception as e:
                print(f'❌ Ошибка при обработке файла {json_file}: {e}')
                continue
        
        # Очистка коллекции перед добавлением новых данных
        words_collection.delete_many({})
        
        # Вставка данных в MongoDB
        if all_documents:
            result = words_collection.insert_many(all_documents)
            print(f'✅ Добавлено {len(result.inserted_ids)} слов из {len(json_files)} файлов')
            return True
        else:
            print('❌ Нет данных для добавления.')
            return False
            
    except Exception as e:
        print(f'❌ Ошибка при добавлении слов: {e}')
        return False
    finally:
        # Закрытие соединения
        if 'client' in locals():
            client.close()

def determine_difficulty(definitions):
    """Определение сложности слова на основе его определений"""
    if not definitions:
        return 'easy'
    
    definition_text = ' '.join(definitions).lower()
    
    if any(keyword in definition_text for keyword in ['разг', 'прост', 'межд', 'част']):
        return 'easy'
    elif any(keyword in definition_text for keyword in ['сущ', 'гл', 'прил', 'нареч']):
        return 'medium'
    else:
        return 'hard'

if __name__ == "__main__":
    print("=== Добавление слов из JSON файлов в MongoDB ===")
    success = add_words_from_json()
    exit(0 if success else 1)