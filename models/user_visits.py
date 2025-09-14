from pymongo import MongoClient
from datetime import datetime, date
import uuid
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
# from config import Config

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'tatar_learning')

class UserVisit:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[DATABASE_NAME]
        self.visits = self.db['visits']
        # Создаем индекс для быстрого поиска по дате
        self.visits.create_index('visit_date')
    
    def track_visit(self):
        """Добавляет запись о посещении, если сегодня еще не было посещений"""
        today = date.today()
        
        # Проверяем, есть ли уже посещение сегодня
        existing_visit = self.visits.find_one({
            'visit_date': today.isoformat()
        })
        
        if existing_visit:
            return None  # Посещение уже было сегодня
        
        # Создаем новую запись
        visit_data = {
            '_id': str(uuid.uuid4()),
            'visit_date': today.isoformat(),  # Сохраняем как строку в формате YYYY-MM-DD
            'created_at': datetime.now()
        }
        
        result = self.visits.insert_one(visit_data)
        return result.inserted_id
    
    def has_visited_today(self):
        """Проверяет, было ли уже посещение сегодня"""
        today = date.today().isoformat()
        return self.visits.find_one({'visit_date': today}) is not None
    
    def get_all_visits(self):
        """Возвращает все посещения"""
        return list(self.visits.find().sort('visit_date', -1))
    
    def get_visits_by_date(self, target_date):
        """Возвращает посещение за определенную дату"""
        return self.visits.find_one({'visit_date': target_date.isoformat()})
    
    def get_visit_count(self):
        """Возвращает общее количество посещений"""
        return self.visits.count_documents({})
    
    def get_visits_by_month(self, year, month):
        """Возвращает посещения за определенный месяц"""
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
        
        # Получаем все даты в формате строк для поиска
        visits = list(self.visits.find({
            'visit_date': {
                '$gte': start_date.isoformat(),
                '$lt': end_date.isoformat()
            }
        }).sort('visit_date', -1))
        
        return visits
    
    def close_connection(self):
        """Закрывает соединение с MongoDB"""
        self.client.close()
