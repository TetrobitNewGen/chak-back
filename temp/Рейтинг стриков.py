"""Теперь нужен рейтинг стрика захода в приложение

Создай массив в который по убыванию выставь: Имя пользователя, его стрик

и так для всех пользователей в  системе, сделай это более многопоточно чтобы подгружать не всех за один запрос"""

"""models.py"""

from pymongo import MongoClient
from datetime import datetime, date, timedelta
import uuid
from concurrent.futures import ThreadPoolExecutor
from config import Config
import math

class UserStreak:
    def __init__(self):
        self.client = MongoClient(Config.MONGO_URI)
        self.db = self.client.get_database()
        self.visits = self.db.streak_visits
        self.streaks = self.db.user_streaks
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Создаем индексы для быстрого поиска
        self.visits.create_index('visit_date')
        self.visits.create_index('user_id')
        self.streaks.create_index('user_id')
        self.streaks.create_index([('current_streak', -1)])
    
    # ... предыдущие методы остаются без изменений ...
    
    def get_streak_ranking(self, page=1, per_page=20, search_query=None):
        """Получает рейтинг стриков с пагинацией"""
        try:
            # Базовый запрос
            query = {}
            if search_query:
                query['user_id'] = {'$regex': f'.*{search_query}.*', '$options': 'i'}
            
            # Общее количество пользователей
            total_users = self.streaks.count_documents(query)
            total_pages = math.ceil(total_users / per_page)
            
            # Получаем данные с пагинацией
            skip = (page - 1) * per_page
            streaks_cursor = (self.streaks.find(query)
                             .sort('current_streak', -1)
                             .skip(skip)
                             .limit(per_page))
            
            streaks_list = list(streaks_cursor)
            
            # Параллельно получаем дополнительную информацию для каждого пользователя
            ranking_data = []
            futures = []
            
            for streak in streaks_list:
                future = self.executor.submit(self._get_user_ranking_data, streak)
                futures.append(future)
            
            # Ждем завершения всех потоков
            for future in futures:
                ranking_data.append(future.result())
            
            return {
                'ranking': ranking_data,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': total_pages,
                    'total_users': total_users,
                    'has_next': page < total_pages,
                    'has_prev': page > 1
                }
            }
            
        except Exception as e:
            print(f"Error in get_streak_ranking: {e}")
            return {
                'ranking': [],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': 0,
                    'total_users': 0,
                    'has_next': False,
                    'has_prev': False
                }
            }
    
    def _get_user_ranking_data(self, streak):
        """Получает данные пользователя для рейтинга (выполняется в отдельном потоке)"""
        try:
            user_id = streak['user_id']
            
            # Получаем количество посещений
            visits_count = self.visits.count_documents({'user_id': user_id})
            
            # Получаем дату последнего посещения
            last_visit = self.visits.find_one(
                {'user_id': user_id},
                sort=[('visit_date', -1)]
            )
            
            # Вычисляем позицию в рейтинге (примерно)
            rank_position = self.streaks.count_documents({
                'current_streak': {'$gt': streak['current_streak']}
            }) + 1
            
            return {
                'user_id': user_id,
                'current_streak': streak['current_streak'],
                'longest_streak': streak['longest_streak'],
                'total_visits': visits_count,
                'last_visit_date': last_visit['visit_date'] if last_visit else None,
                'rank_position': rank_position,
                'start_date': streak.get('start_date'),
                'is_active_today': self._is_active_today(user_id)
            }
        except Exception as e:
            print(f"Error in _get_user_ranking_data for {streak.get('user_id')}: {e}")
            return {
                'user_id': streak.get('user_id', 'unknown'),
                'current_streak': streak.get('current_streak', 0),
                'longest_streak': streak.get('longest_streak', 0),
                'total_visits': 0,
                'last_visit_date': None,
                'rank_position': 0,
                'start_date': None,
                'is_active_today': False
            }
    
    def _is_active_today(self, user_id):
        """Проверяет, был ли пользователь активен сегодня"""
        today = date.today().isoformat()
        return self.visits.find_one({
            'user_id': user_id,
            'visit_date': today
        }) is not None
    
    def get_top_streaks(self, limit=10):
        """Получает топ-N стриков"""
        try:
            top_streaks = list(self.streaks.find()
                              .sort('current_streak', -1)
                              .limit(limit))
            
            # Параллельная обработка топовых пользователей
            top_data = []
            futures = []
            
            for streak in top_streaks:
                future = self.executor.submit(self._get_user_ranking_data, streak)
                futures.append(future)
            
            for future in futures:
                result = future.result()
                result['rank_position'] = len(top_data) + 1  # Точная позиция в топе
                top_data.append(result)
            
            return top_data
            
        except Exception as e:
            print(f"Error in get_top_streaks: {e}")
            return []
    
    def get_user_rank(self, user_id):
        """Получает позицию конкретного пользователя в рейтинге"""
        try:
            user_streak = self.streaks.find_one({'user_id': user_id})
            if not user_streak:
                return None
            
            # Количество пользователей с большим стриком + 1
            rank_position = self.streaks.count_documents({
                'current_streak': {'$gt': user_streak['current_streak']}
            }) + 1
            
            user_data = self._get_user_ranking_data(user_streak)
            user_data['rank_position'] = rank_position
            
            return user_data
            
        except Exception as e:
            print(f"Error in get_user_rank: {e}")
            return None
    
    def close_connection(self):
        """Закрывает соединение с MongoDB и executor"""
        self.executor.shutdown(wait=True)
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
        'message': 'User Streak Tracking API with Ranking',
        'description': 'Система отслеживания стриков с рейтингом пользователей',
        'endpoints': {
            'track_visit': '/api/streak/visit',
            'get_streak': '/api/streak',
            'get_history': '/api/streak/history',
            'get_ranking': '/api/ranking',
            'get_top': '/api/ranking/top',
            'get_user_rank': '/api/ranking/user',
            'get_all_streaks': '/api/streak/all',
            'reset_streak': '/api/streak/reset'
        }
    })

# ... предыдущие endpoints остаются без изменений ...

@app.route('/api/ranking', methods=['GET'])
def get_streak_ranking():
    """Получает рейтинг стриков с пагинацией"""
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', None)
        
        if page < 1:
            page = 1
        if per_page < 1 or per_page > 100:
            per_page = 20
        
        ranking_data = streak_model.get_streak_ranking(page, per_page, search)
        
        return jsonify({
            'success': True,
            'ranking': ranking_data['ranking'],
            'pagination': ranking_data['pagination'],
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ranking/top', methods=['GET'])
def get_top_streaks():
    """Получает топ стриков"""
    try:
        limit = int(request.args.get('limit', 10))
        
        if limit < 1 or limit > 50:
            limit = 10
        
        top_streaks = streak_model.get_top_streaks(limit)
        
        return jsonify({
            'success': True,
            'top_streaks': top_streaks,
            'limit': limit,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/ranking/user', methods=['GET'])
def get_user_rank():
    """Получает позицию конкретного пользователя в рейтинге"""
    try:
        user_id = request.args.get('user_id', 'default_user')
        
        user_rank = streak_model.get_user_rank(user_id)
        
        if not user_rank:
            return jsonify({
                'success': False,
                'error': 'User not found in ranking'
            }), 404
        
        return jsonify({
            'success': True,
            'user_rank': user_rank,
            'timestamp': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ... остальные endpoints ...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
