"""BackEnd на Flask с Mongodb, храни в коллекции максимальные стрики пользователей, но перед записью проверяй лучше ли стрик у него получился или хуже"""

"app.py"
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import logging
import re
from config import Config

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)  # Разрешаем запросы с фронтенда

# Подключение к MongoDB
try:
    client = MongoClient(app.config['MONGO_URI'])
    db = client.get_database()
    streaks_collection = db['user_streaks']
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise e

class JSONEncoder:
    """Custom JSON encoder for handling ObjectId"""
    @staticmethod
    def encode(data):
        if isinstance(data, list):
            return [JSONEncoder.encode(item) for item in data]
        elif isinstance(data, dict):
            return {key: JSONEncoder.encode(value) for key, value in data.items()}
        elif isinstance(data, ObjectId):
            return str(data)
        elif isinstance(data, datetime):
            return data.isoformat()
        return data

def validate_user_id(user_id):
    """Валидация user_id"""
    if not user_id or not isinstance(user_id, str):
        return False
    # Минимальная валидация - не пустая строка
    return len(user_id.strip()) > 0

def validate_streak(streak):
    """Валидация значения стрика"""
    try:
        streak_int = int(streak)
        return streak_int >= 0  # Стрик не может быть отрицательным
    except (ValueError, TypeError):
        return False

@app.route('/api/streak', methods=['POST'])
def update_streak():
    """
    Обновляет максимальный стрик пользователя.
    Данные приходят с фронтенда в формате JSON.
    """
    try:
        # Проверяем Content-Type
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400
        
        data = request.get_json()
        
        # Логируем полученные данные для отладки
        logger.info(f"Received data from frontend: {data}")
        
        # Валидация обязательных полей
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        user_id = data.get('user_id')
        current_streak = data.get('current_streak')
        streak_name = data.get('streak_name')  # Опциональное поле для типа стрика
        
        # Валидация user_id
        if not validate_user_id(user_id):
            return jsonify({
                'success': False,
                'error': 'Invalid user_id format'
            }), 400
        
        # Валидация стрика
        if not validate_streak(current_streak):
            return jsonify({
                'success': False,
                'error': 'Invalid streak value. Must be a non-negative integer'
            }), 400
        
        current_streak = int(current_streak)
        
        # Поиск текущего максимального стрика пользователя
        query = {'user_id': user_id}
        if streak_name:
            query['streak_name'] = streak_name
        
        existing_streak = streaks_collection.find_one(query)
        
        if existing_streak:
            max_streak = existing_streak.get('max_streak', 0)
            
            # Проверяем, лучше ли новый стрик
            if current_streak > max_streak:
                # Обновляем максимальный стрик
                update_data = {
                    'max_streak': current_streak,
                    'last_updated': datetime.utcnow(),
                    'previous_max': max_streak
                }
                
                streaks_collection.update_one(
                    query,
                    {'$set': update_data}
                )
                
                logger.info(f"User {user_id} improved streak from {max_streak} to {current_streak}")
                
                return jsonify({
                    'success': True,
                    'message': 'Streak improved!',
                    'previous_streak': max_streak,
                    'new_streak': current_streak,
                    'improved': True
                }), 200
            else:
                logger.info(f"User {user_id} current streak {current_streak} not better than max {max_streak}")
                
                return jsonify({
                    'success': True,
                    'message': 'Current streak not better than maximum',
                    'current_streak': current_streak,
                    'max_streak': max_streak,
                    'improved': False
                }), 200
        else:
            # Создаем новую запись для пользователя
            new_streak = {
                'user_id': user_id,
                'max_streak': current_streak,
                'last_updated': datetime.utcnow(),
                'created_at': datetime.utcnow(),
                'previous_max': 0
            }
            
            # Добавляем название стрика если provided
            if streak_name:
                new_streak['streak_name'] = streak_name
            
            streaks_collection.insert_one(new_streak)
            logger.info(f"Created new streak record for user {user_id} with streak {current_streak}")
            
            return jsonify({
                'success': True,
                'message': 'New streak record created',
                'max_streak': current_streak,
                'improved': True
            }), 201
            
    except Exception as e:
        logger.error(f"Error updating streak: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/streak/<user_id>', methods=['GET'])
def get_user_streaks(user_id):
    """
    Получает все стрики пользователя или конкретный стрик по имени
    """
    try:
        streak_name = request.args.get('streak_name')
        
        query = {'user_id': user_id}
        if streak_name:
            query['streak_name'] = streak_name
        
        streaks = list(streaks_collection.find(query))
        
        if not streaks:
            return jsonify({
                'success': True,
                'message': 'No streak records found',
                'data': [],
                'exists': False
            }), 200
        
        response_data = JSONEncoder.encode(streaks)
        
        return jsonify({
            'success': True,
            'exists': True,
            'count': len(response_data),
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user streaks: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/streak/stats', methods=['GET'])
def get_streak_stats():
    """
    Получает статистику по стрикам
    """
    try:
        user_id = request.args.get('user_id')
        streak_name = request.args.get('streak_name')
        
        if not user_id:
            return jsonify({
                'success': False,
                'error': 'user_id parameter is required'
            }), 400
        
        query = {'user_id': user_id}
        if streak_name:
            query['streak_name'] = streak_name
        
        streak_data = streaks_collection.find_one(query)
        
        if not streak_data:
            return jsonify({
                'success': True,
                'exists': False,
                'message': 'No streak data found'
            }), 200
        
        # Рассчитываем длительность текущего стрика
        last_updated = streak_data.get('last_updated', datetime.utcnow())
        days_since_update = (datetime.utcnow() - last_updated).days
        
        response_data = JSONEncoder.encode(streak_data)
        response_data['days_since_update'] = days_since_update
        
        return jsonify({
            'success': True,
            'exists': True,
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting streak stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/streaks/top', methods=['GET'])
def get_top_streaks():
    """
    Получает топ-N пользователей с наибольшими стриками
    """
    try:
        limit = int(request.args.get('limit', 10))
        streak_name = request.args.get('streak_name')
        
        query = {}
        if streak_name:
            query['streak_name'] = streak_name
        
        top_streaks = list(streaks_collection.find(query)
                          .sort('max_streak', -1)
                          .limit(limit))
        
        response_data = JSONEncoder.encode(top_streaks)
        
        return jsonify({
            'success': True,
            'count': len(response_data),
            'data': response_data
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting top streaks: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья приложения
    """
    try:
        client.admin.command('ping')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)