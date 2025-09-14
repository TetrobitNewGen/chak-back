"""Теперь отдельно напиши мне хранение стрика захода в приложение пользователя используя коллекцию с хранением дней захода. Если он несколько дней подряд заходит 
у него стрик, если он пропустил один день то стрик обнуляется"""


"""models.py"""

from pymongo import MongoClient
from datetime import datetime, date, timedelta
import uuid
from config import Config

class UserStreak:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client.get_database()
        self.visits = self.db.streak_visits
        self.streaks = self.db.user_streaks
        
        # Создаем индексы для быстрого поиска
        self.visits.create_index('visit_date')
        self.visits.create_index('user_id')
        self.streaks.create_index('user_id')
    
    def track_visit(self, user_id="default_user"):
        """Добавляет запись о посещении и обновляет стрик"""
        today = date.today()
        
        # Проверяем, есть ли уже посещение сегодня
        existing_visit = self.visits.find_one({
            'user_id': user_id,
            'visit_date': today.isoformat()
        })
        
        if existing_visit:
            return self._get_streak_info(user_id)  # Посещение уже было сегодня
        
        # Добавляем новое посещение
        visit_data = {
            '_id': str(uuid.uuid4()),
            'user_id': user_id,
            'visit_date': today.isoformat(),
            'created_at': datetime.now()
        }
        self.visits.insert_one(visit_data)
        
        # Обновляем стрик
        return self._update_streak(user_id)
    
    def _update_streak(self, user_id):
        """Обновляет стрик пользователя"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        # Получаем текущий стрик
        current_streak = self.streaks.find_one({'user_id': user_id})
        
        if not current_streak:
            # Первое посещение - создаем новый стрик
            streak_data = {
                '_id': str(uuid.uuid4()),
                'user_id': user_id,
                'current_streak': 1,
                'longest_streak': 1,
                'last_visit_date': today.isoformat(),
                'start_date': today.isoformat(),
                'updated_at': datetime.now()
            }
            self.streaks.insert_one(streak_data)
            return self._get_streak_info(user_id)
        
        last_visit = datetime.strptime(current_streak['last_visit_date'], '%Y-%m-%d').date()
        
        if last_visit == yesterday:
            # Последовательные дни - увеличиваем стрик
            new_streak = current_streak['current_streak'] + 1
            longest_streak = max(current_streak['longest_streak'], new_streak)
            
            self.streaks.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'current_streak': new_streak,
                        'longest_streak': longest_streak,
                        'last_visit_date': today.isoformat(),
                        'updated_at': datetime.now()
                    }
                }
            )
        elif last_visit == today:
            # Уже было посещение сегодня
            pass
        else:
            # Пропущен день - обнуляем стрик
            self.streaks.update_one(
                {'user_id': user_id},
                {
                    '$set': {
                        'current_streak': 1,
                        'last_visit_date': today.isoformat(),
                        'start_date': today.isoformat(),
                        'updated_at': datetime.now()
                    }
                }
            )
        
        return self._get_streak_info(user_id)
    
    def _get_streak_info(self, user_id):
        """Получает информацию о стрике пользователя"""
        streak = self.streaks.find_one({'user_id': user_id})
        visits = list(self.visits.find({'user_id': user_id}).sort('visit_date', -1))
        
        if not streak:
            return {
                'current_streak': 0,
                'longest_streak': 0,
                'total_visits': 0,
                'last_visit_date': None,
                'start_date': None
            }
        
        return {
            'current_streak': streak['current_streak'],
            'longest_streak': streak['longest_streak'],
            'total_visits': len(visits),
            'last_visit_date': streak['last_visit_date'],
            'start_date': streak.get('start_date'),
            'visits_count': len(visits)
        }
    
    def get_streak_info(self, user_id="default_user"):
        """Получает полную информацию о стрике"""
        return self._get_streak_info(user_id)
    
    def get_visit_history(self, user_id="default_user", limit=30):
        """Возвращает историю посещений"""
        visits = list(self.visits.find({'user_id': user_id})
                     .sort('visit_date', -1)
                     .limit(limit))
        
        serialized_visits = []
        for visit in visits:
            serialized_visits.append({
                'id': str(visit['_id']),
                'visit_date': visit['visit_date'],
                'created_at': visit['created_at'].isoformat()
            })
        
        return serialized_visits
    
    def get_all_streaks(self):
        """Возвращает все стрики (для админки)"""
        streaks = list(self.streaks.find().sort('current_streak', -1))
        
        serialized_streaks = []
        for streak in streaks:
            visits_count = self.visits.count_documents({'user_id': streak['user_id']})
            serialized_streaks.append({
                'user_id': streak['user_id'],
                'current_streak': streak['current_streak'],
                'longest_streak': streak['longest_streak'],
                'last_visit_date': streak['last_visit_date'],
                'start_date': streak.get('start_date'),
                'total_visits': visits_count
            })
        
        return serialized_streaks
    
    def reset_streak(self, user_id="default_user"):
        """Сбрасывает стрик пользователя (для тестирования)"""
        self.streaks.delete_one({'user_id': user_id})
        return True
    
    def close_connection(self):
        """Закрывает соединение с MongoDB"""
        self.client.close()


"""app.py"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from models import UserStreak
from datetime import datetime, date
import json

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Инициализируем модель для работы со стриками
streak_model = UserStreak()

@app.route('/')
def home():
    return jsonify({
        'message': 'User Streak Tracking API',
        'description': 'Система отслеживания последовательных дней заходов (стриков)',
        'endpoints': {
            'track_visit': '/api/streak/visit',
            'get_streak': '/api/streak',
            'get_history': '/api/streak/history',
            'get_all_streaks': '/api/streak/all',
            'reset_streak': '/api/streak/reset'
        }
    })

@app.route('/api/streak/visit', methods=['POST', 'GET'])
def track_streak_visit():
    """Отслеживает посещение и обновляет стрик"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        result = streak_model.track_visit(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Visit tracked successfully',
            'user_id': user_id,
            'streak_info': result,
            'today': date.today().isoformat()
        }), 200
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/streak', methods=['GET'])
def get_streak_info():
    """Получает информацию о текущем стрике"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        streak_info = streak_model.get_streak_info(user_id)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'streak_info': streak_info,
            'today': date.today().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/streak/history', methods=['GET'])
def get_visit_history():
    """Возвращает историю посещений"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        limit = int(request.args.get('limit', 30))
        
        history = streak_model.get_visit_history(user_id, limit)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'history': history,
            'total_count': len(history)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/streak/all', methods=['GET'])
def get_all_streaks():
    """Возвращает все стрики (для админки)"""
    try:
        streaks = streak_model.get_all_streaks()
        
        return jsonify({
            'success': True,
            'total_users': len(streaks),
            'streaks': streaks
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/streak/reset', methods=['POST'])
def reset_streak():
    """Сбрасывает стрик пользователя (для тестирования)"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        success = streak_model.reset_streak(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Streak reset successfully',
            'user_id': user_id
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