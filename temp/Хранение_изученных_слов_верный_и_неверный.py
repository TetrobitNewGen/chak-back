from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import json
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# MongoDB connection
client = MongoClient(app.config['MONGO_URI'])
db = client.get_database()
answers_collection = db['answers']

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)

app.json_encoder = JSONEncoder

@app.route('/api/user-answers/<user_id>', methods=['GET'])
def get_user_answers(user_id):
    """
    Получает ответы пользователя и разделяет на правильные и неправильные
    """
    try:
        # Получаем все ответы пользователя
        user_answers = list(answers_collection.find({'user_id': user_id}))
        
        if not user_answers:
            return jsonify({
                'success': True,
                'message': 'No answers found for this user',
                'correct_words': [],
                'incorrect_words': []
            }), 200
        
        # Разделяем слова на правильные и неправильные
        correct_words = []
        incorrect_words = []
        
        for answer in user_answers:
            word_data = {
                'word': answer.get('word'),
                'answer': answer.get('answer'),
                'timestamp': answer.get('timestamp')
            }
            
            if answer.get('answer') == 'верный':
                correct_words.append(word_data)
            elif answer.get('answer') == 'неверный':
                incorrect_words.append(word_data)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'total_answers': len(user_answers),
            'correct_answers': len(correct_words),
            'incorrect_answers': len(incorrect_words),
            'correct_words': correct_words,
            'incorrect_words': incorrect_words
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/user-answers/stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    """
    Получает статистику ответов пользователя
    """
    try:
        # Получаем все ответы пользователя
        user_answers = list(answers_collection.find({'user_id': user_id}))
        
        if not user_answers:
            return jsonify({
                'success': True,
                'message': 'No answers found for this user',
                'stats': {
                    'total': 0,
                    'correct': 0,
                    'incorrect': 0,
                    'accuracy': 0
                }
            }), 200
        
        correct_count = sum(1 for answer in user_answers if answer.get('answer') == 'верный')
        incorrect_count = sum(1 for answer in user_answers if answer.get('answer') == 'неверный')
        accuracy = (correct_count / len(user_answers)) * 100 if user_answers else 0
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'stats': {
                'total': len(user_answers),
                'correct': correct_count,
                'incorrect': incorrect_count,
                'accuracy': round(accuracy, 2)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/answers', methods=['POST'])
def add_answer():

    """
    Это уже так для души если надо
    """
    """
    Добавляет новый ответ пользователя
    """
    try:
        data = request.get_json()
        
        if not data or 'user_id' not in data or 'word' not in data or 'answer' not in data:
            return jsonify({
                'success': False,
                'error': 'Missing required fields: user_id, word, answer'
            }), 400
        
        # Проверяем допустимые значения ответа
        if data['answer'] not in ['верный', 'неверный']:
            return jsonify({
                'success': False,
                'error': 'Answer must be either "верный" or "неверный"'
            }), 400
        
        # Добавляем timestamp
        from datetime import datetime
        data['timestamp'] = datetime.utcnow()
        
        # Вставляем запись в базу данных
        result = answers_collection.insert_one(data)
        
        return jsonify({
            'success': True,
            'message': 'Answer added successfully',
            'answer_id': str(result.inserted_id)
        }), 201
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/answers/<answer_id>', methods=['DELETE'])
def delete_answer(answer_id):
    """
    Удаляет ответ по ID
    """
    try:
        result = answers_collection.delete_one({'_id': ObjectId(answer_id)})
        
        if result.deleted_count == 0:
            return jsonify({
                'success': False,
                'error': 'Answer not found'
            }), 404
        
        return jsonify({
            'success': True,
            'message': 'Answer deleted successfully'
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