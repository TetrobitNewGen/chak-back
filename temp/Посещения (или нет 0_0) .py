# Напиши backend часть которая сделана на python flask с использованием mongodb, от тебя требуется при заходе пользователя  в приложение добавлять в бд его дату захода

# ip adress не нужен

# Нужен заход именно в конкретный день и он записывается только один раз, дальнейшие заходы уже не учитываются в этот же день, так же а зачем timestamp

# Итог

"""models.py"""

from pymongo import MongoClient
from datetime import datetime, date
import uuid
import os
# from config import Config

MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'tatar_learning')
# users_collection = db['users']
# client = MongoClient(MONGODB_URI)
# db = client[DATABASE_NAME]

class UserVisit:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = os.getenv('DATABASE_NAME', 'tatar_learning')
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

       

from flask import Flask, request, jsonify
from flask_cors import CORS
from models import UserVisit
from datetime import datetime, date
import json

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Инициализируем модель для работы с посещениями
visit_model = UserVisit()

@app.route('/')
def home():
    return jsonify({
        'message': 'Daily Visit Tracker API',
        'description': 'Записывает только одно посещение в день',
        'endpoints': {
            'track_visit': '/api/visit',
            'check_today': '/api/visit/today',
            'get_visits': '/api/visits',
            'get_stats': '/api/stats',
            'get_month_visits': '/api/visits/<year>/<month>'
        }
    })

@app.route('/api/visit', methods=['POST', 'GET'])
def track_visit():
    """Отслеживает посещение пользователя (только одно в день)"""
    try:
        # Проверяем, было ли уже посещение сегодня
        if visit_model.has_visited_today():
            return jsonify({
                'success': True,
                'message': 'Visit already recorded today',
                'already_visited': True,
                'visit_date': date.today().isoformat()
            }), 200
        
        # Добавляем запись о посещении
        visit_id = visit_model.track_visit()
        
        if visit_id:
            return jsonify({
                'success': True,
                'message': 'Visit tracked successfully',
                'visit_id': str(visit_id),
                'visit_date': date.today().isoformat(),
                'already_visited': False
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to track visit'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/visit/today', methods=['GET'])
def check_today_visit():
    """Проверяет, было ли уже посещение сегодня"""
    try:
        has_visited = visit_model.has_visited_today()
        
        return jsonify({
            'success': True,
            'has_visited_today': has_visited,
            'today': date.today().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/visits', methods=['GET'])
def get_visits():
    """Возвращает список всех посещений"""
    try:
        visits = visit_model.get_all_visits()
        
        # Преобразуем для JSON сериализации
        serialized_visits = []
        for visit in visits:
            serialized_visit = {
                'id': str(visit['_id']),
                'visit_date': visit['visit_date'],
                'created_at': visit['created_at'].isoformat() if 'created_at' in visit else None
            }
            serialized_visits.append(serialized_visit)
        
        return jsonify({
            'success': True,
            'visits': serialized_visits,
            'total_visits': len(serialized_visits)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/visits/<int:year>/<int:month>', methods=['GET'])
def get_month_visits(year, month):
    """Возвращает посещения за определенный месяц"""
    try:
        if month < 1 or month > 12:
            return jsonify({
                'success': False,
                'error': 'Month must be between 1 and 12'
            }), 400
        
        visits = visit_model.get_visits_by_month(year, month)
        
        serialized_visits = []
        for visit in visits:
            serialized_visit = {
                'id': str(visit['_id']),
                'visit_date': visit['visit_date'],
                'created_at': visit['created_at'].isoformat() if 'created_at' in visit else None
            }
            serialized_visits.append(serialized_visit)
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'visits': serialized_visits,
            'total_visits': len(serialized_visits)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Возвращает статистику посещений"""
    try:
        total_visits = visit_model.get_visit_count()
        has_visited_today = visit_model.has_visited_today()
        
        # Получаем все посещения для анализа
        all_visits = visit_model.get_all_visits()
        
        # Анализируем посещения по месяцам
        monthly_stats = {}
        for visit in all_visits:
            visit_date = datetime.strptime(visit['visit_date'], '%Y-%m-%d')
            month_key = f"{visit_date.year}-{visit_date.month:02d}"
            
            if month_key in monthly_stats:
                monthly_stats[month_key] += 1
            else:
                monthly_stats[month_key] = 1
        
        # Сортируем по дате
        sorted_months = sorted(monthly_stats.items(), reverse=True)
        
        return jsonify({
            'success': True,
            'total_visits': total_visits,
            'has_visited_today': has_visited_today,
            'today': date.today().isoformat(),
            'monthly_stats': dict(sorted_months),
            'unique_days': total_visits  # Каждое посещение - уникальный день
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)