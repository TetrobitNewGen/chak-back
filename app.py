from flask import Flask, request, jsonify
from pymongo import MongoClient
from flask_cors import CORS
import uuid
import os
from datetime import datetime
from bson import ObjectId

app = Flask(__name__)
CORS(app)

# Подключение к MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['tatar_learning']

# Коллекции
users_collection = db['users']
cards_collection = db['cards']
answers_collection = db['answers']

@app.route('/register', methods=['POST'])
def register():
    '''Регистрация нового пользователя с UUID и токеном'''
    user_id = str(uuid.uuid4())
    token = str(uuid.uuid4())
    
    user_data = {
        'user_id': user_id,
        'token': token,
        'created_at': datetime.utcnow(),
        'total_questions': 0,
        'correct_answers': 0,
        'current_streak': 0,
        'max_streak': 0,
        'last_login': None
    }
    
    users_collection.insert_one(user_data)
    
    return jsonify({
        'success': True,
        'user_id': user_id,
        'token': token
    })

@app.route('/cards', methods=['GET'])
def get_cards():
    '''Получение списка карточек с татарскими словами и переводами'''
    cards = list(cards_collection.find({}, {'_id': 0}))
    return jsonify({
        'success': True,
        'cards': cards
    })

@app.route('/answer', methods=['POST'])
def submit_answer():
    '''Отправка ответа пользователя на карточку'''
    data = request.get_json()
    user_id = data.get('user_id')
    token = data.get('token')
    card_id = data.get('card_id')
    is_correct = data.get('is_correct')
    
    # Проверка пользователя
    user = users_collection.find_one({'user_id': user_id, 'token': token})
    if not user:
        return jsonify({'success': False, 'error': 'Invalid user'}), 401
    
    # Сохранение ответа
    answer_data = {
        'user_id': user_id,
        'card_id': card_id,
        'is_correct': is_correct,
        'answered_at': datetime.utcnow()
    }
    
    answers_collection.insert_one(answer_data)
    
    # Обновление статистики пользователя
    update_data = {
        '': {'total_questions': 1}
    }
    
    if is_correct:
        update_data['']['correct_answers'] = 1
        update_data['']['current_streak'] = 1
        update_data[''] = {'max_streak': user.get('current_streak', 0) + 1}
    else:
        update_data[''] = {'current_streak': 0}
    
    users_collection.update_one(
        {'user_id': user_id}, 
        update_data
    )
    
    return jsonify({'success': True})

@app.route('/rating/words', methods=['GET'])
def get_rating_by_words():
    '''Рейтинг по количеству изученных слов'''
    pipeline = [
        {
            '': {
                'from': 'answers',
                'localField': 'user_id',
                'foreignField': 'user_id',
                'as': 'answers'
            }
        },
        {
            '': {
                'correct_words': {
                    '': {
                        '': {
                            'input': '',
                            'cond': {'': ['app.pythis.is_correct', True]}
                        }
                    }
                }
            }
        },
        {
            '': {'correct_words': -1}
        },
        {
            '': {
                'user_id': 1,
                'correct_words': 1,
                '_id': 0
            }
        }
    ]
    
    rating = list(users_collection.aggregate(pipeline))
    return jsonify({
        'success': True,
        'rating': rating
    })

@app.route('/rating/streak', methods=['GET'])
def get_rating_by_streak():
    '''Рейтинг по максимальному стрику'''
    users = list(users_collection.find(
        {}, 
        {'user_id': 1, 'max_streak': 1, '_id': 0}
    ).sort('max_streak', -1))
    
    return jsonify({
        'success': True,
        'rating': users
    })

@app.route('/stats/<user_id>', methods=['GET'])
def get_user_stats(user_id):
    '''Получение статистики конкретного пользователя'''
    user = users_collection.find_one(
        {'user_id': user_id}, 
        {'_id': 0, 'token': 0}
    )
    
    if not user:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'stats': user
    })

if __name__ == '__main__':
    # Создание тестовых карточек при запуске
    if cards_collection.count_documents({}) == 0:
        test_cards = [
            {
                'card_id': str(uuid.uuid4()),
                'tatar_word': 'сәлам',
                'russian_translation': 'привет',
                'difficulty': 'easy'
            },
            {
                'card_id': str(uuid.uuid4()),
                'tatar_word': 'рәхмәт',
                'russian_translation': 'спасибо',
                'difficulty': 'easy'
            },
            {
                'card_id': str(uuid.uuid4()),
                'tatar_word': 'китап',
                'russian_translation': 'книга',
                'difficulty': 'medium'
            },
            {
                'card_id': str(uuid.uuid4()),
                'tatar_word': 'өй',
                'russian_translation': 'дом',
                'difficulty': 'easy'
            },
            {
                'card_id': str(uuid.uuid4()),
                'tatar_word': 'мәктәп',
                'russian_translation': 'школа',
                'difficulty': 'medium'
            }
        ]
        cards_collection.insert_many(test_cards)
        print('Тестовые карточки созданы!')
    
    app.run(debug=True, host='0.0.0.0', port=5000)
