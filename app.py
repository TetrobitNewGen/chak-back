from flask import Flask, request, jsonify, Response
from pymongo import MongoClient
from flask_cors import CORS
from flasgger import Swagger, swag_from
import uuid
import os
import re
import json
import random
from datetime import datetime
from bson import ObjectId
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

app = Flask(__name__)
CORS(app)

# Настройка Swagger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'apispec_1',
            "route": '/apispec_1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Татарский язык - API для изучения",
        "description": "API для изучения татарского языка с карточками, статистикой и рейтингами",
        "version": "1.0.0",
        "contact": {
            "name": "API Support",
            "email": "support@example.com"
        }
    },
    "host": "localhost:5000",
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Получение конфигурации из .env
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'tatar_learning')
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))

# Подключение к MongoDB
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

# Коллекции
users_collection = db['users']
cards_collection = db['cards']
words_collection = db['words']
answers_collection = db['answers']

REMOVE_WORDS_1 = ['разг', 'прост', 'межд', 'част']
REMOVE_WORDS_2 = ['сущ', 'гл', 'прил', 'нареч', 'пр']

@app.route('/register', methods=['POST'])
def register():
    """
    Регистрация нового пользователя
    ---
    tags:
      - Пользователи
    summary: Создание нового пользователя
    description: Создает нового пользователя с UUID и токеном для доступа
    responses:
      200:
        description: Пользователь успешно зарегистрирован
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            user_id:
              type: string
              format: uuid
              example: "123e4567-e89b-12d3-a456-426614174000"
            token:
              type: string
              format: uuid
              example: "987fcdeb-51a2-43d1-b789-123456789abc"
    """
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
def get_random_words():
    """
    Получение 100 случайных слов с обработкой определений
    ---
    tags:
      - Слова
    summary: Получить 100 случайных слов
    description: |
      Возвращает 100 случайных слов из базы данных с обработкой определений.
      
      Правила обработки:
      - Если определение содержит "1.", оно заменяется на определение из случайного другого слова
      - Удаляются служебные слова: разг, прост, межд, част, сущ, гл, прил, нареч, пр
    responses:
      200:
        description: Успешный запрос, возвращает 100 случайных слов
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            words:
              type: array
              items:
                type: object
                properties:
                  word:
                    type: string
                    example: "сәлам"
                  definitions:
                    type: array
                    items:
                      type: string
                    example: ["приветствие", "здравствуйте"]
                  difficulty:
                    type: string
                    enum: [easy, medium, hard]
                    example: "easy"
      500:
        description: Ошибка сервера
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Internal server error"
    """
    try:
        # Получаем 100 случайных слов
        words = list(words_collection.aggregate([
            {'$sample': {'size': 100}}
        ]))
        
        # Получаем все слова для возможной замены определений
        all_words = list(words_collection.find({}, {'definitions': 1}))
        
        processed_words = []
        
        for word in words:
            processed_word = {
                'word': word.get('word', ''),
                'definitions': word.get('definitions', []),
                'difficulty': word.get('difficulty', 'easy')
            }
            
            # Проверяем, содержит ли definitions "1."
            contains_numbered = any('1.' in definition for definition in processed_word['definitions'])
            
            # Если содержит, заменяем definitions на случайные из другого слова
            if contains_numbered and all_words:
                # Выбираем случайное слово (исключая текущее)
                other_words = [w for w in all_words if w['_id'] != word['_id']]
                if other_words:
                    random_word = random.choice(other_words)
                    processed_word['definitions'] = random_word.get('definitions', [])
            
            # Удаляем нежелательные слова из definitions
            filtered_definitions = []
            for definition in processed_word['definitions']:
                # Удаляем слова из первого списка
                for word_to_remove in REMOVE_WORDS_1:
                    definition = re.sub(r'\b' + word_to_remove + r'\b', '', definition, flags=re.IGNORECASE)
                
                # Удаляем слова из второго списка
                for word_to_remove in REMOVE_WORDS_2:
                    definition = re.sub(r'\b' + word_to_remove + r'\b', '', definition, flags=re.IGNORECASE)
                
                # Очищаем от лишних пробелов и запятых
                definition = re.sub(r'\s+', ' ', definition).strip()
                definition = re.sub(r'^,\s*|\s*,$', '', definition)
                
                # Добавляем только непустые определения
                if definition:
                    filtered_definitions.append(definition)
            
            processed_word['definitions'] = filtered_definitions
            
            # Добавляем обработанное слово в результат
            processed_words.append(processed_word)
        
          # Создаем ответ с правильной кодировкой
        response_data = json.dumps({
            'success': True,
            'words': processed_words
        }, ensure_ascii=False)
        
        return Response(response_data, mimetype='application/json; charset=utf-8')
        
    except Exception as e:
        error_response = json.dumps({
            'success': False,
            'error': str(e)
        }, ensure_ascii=False)
        
        return Response(error_response, status=500, mimetype='application/json; charset=utf-8')

@app.route('/answer', methods=['POST'])
def submit_answer():
    """
    Отправка ответа на карточку
    ---
    tags:
      - Ответы
    summary: Отправить ответ пользователя
    description: Отправляет ответ пользователя на карточку и обновляет статистику
    parameters:
      - in: body
        name: answer_data
        required: true
        schema:
          type: object
          required:
            - user_id
            - token
            - card_id
            - is_correct
          properties:
            user_id:
              type: string
              format: uuid
              example: "123e4567-e89b-12d3-a456-426614174000"
            token:
              type: string
              format: uuid
              example: "987fcdeb-51a2-43d1-b789-123456789abc"
            card_id:
              type: string
              format: uuid
              example: "456e7890-e89b-12d3-a456-426614174001"
            is_correct:
              type: boolean
              example: true
    responses:
      200:
        description: Ответ успешно сохранен
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
      401:
        description: Неверный пользователь или токен
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Invalid user"
    """
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
    """
    Рейтинг по изученным словам
    ---
    tags:
      - Рейтинги
    summary: Получить рейтинг пользователей по количеству изученных слов
    description: Возвращает рейтинг пользователей, отсортированный по количеству правильно изученных слов
    responses:
      200:
        description: Рейтинг успешно получен
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            rating:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    type: string
                    format: uuid
                    example: "123e4567-e89b-12d3-a456-426614174000"
                  correct_words:
                    type: integer
                    example: 15
    """
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
                            'cond': {'': ['requirements.txtthis.is_correct', True]}
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
    """
    Рейтинг по максимальному стрику
    ---
    tags:
      - Рейтинги
    summary: Получить рейтинг пользователей по максимальному стрику
    description: Возвращает рейтинг пользователей, отсортированный по максимальному стрику правильных ответов подряд
    responses:
      200:
        description: Рейтинг успешно получен
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            rating:
              type: array
              items:
                type: object
                properties:
                  user_id:
                    type: string
                    format: uuid
                    example: "123e4567-e89b-12d3-a456-426614174000"
                  max_streak:
                    type: integer
                    example: 8
    """
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
    """
    Статистика пользователя
    ---
    tags:
      - Статистика
    summary: Получить статистику конкретного пользователя
    description: Возвращает подробную статистику пользователя по изучению татарского языка
    parameters:
      - in: path
        name: user_id
        type: string
        format: uuid
        required: true
        description: UUID пользователя
        example: "123e4567-e89b-12d3-a456-426614174000"
    responses:
      200:
        description: Статистика успешно получена
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: true
            stats:
              type: object
              properties:
                user_id:
                  type: string
                  format: uuid
                  example: "123e4567-e89b-12d3-a456-426614174000"
                total_questions:
                  type: integer
                  example: 25
                correct_answers:
                  type: integer
                  example: 20
                current_streak:
                  type: integer
                  example: 5
                max_streak:
                  type: integer
                  example: 12
                created_at:
                  type: string
                  format: date-time
                  example: "2023-09-13T10:30:00Z"
                last_login:
                  type: string
                  format: date-time
                  example: "2023-09-13T15:45:00Z"
      404:
        description: Пользователь не найден
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "User not found"
    """
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

@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка состояния API
    ---
    tags:
      - Система
    summary: Проверка работоспособности API
    description: Простая проверка, что API работает
    responses:
      200:
        description: API работает
        schema:
          type: object
          properties:
            status:
              type: string
              example: "OK"
            timestamp:
              type: string
              format: date-time
              example: "2023-09-13T10:30:00Z"
    """
    return jsonify({
        'status': 'OK',
        'timestamp': datetime.utcnow().isoformat()
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
    
    print(f'Запуск сервера на {FLASK_HOST}:{FLASK_PORT}')
    print(f'Swagger документация доступна по адресу: http://{FLASK_HOST}:{FLASK_PORT}/docs')
    app.run(debug=True, host=FLASK_HOST, port=FLASK_PORT)
