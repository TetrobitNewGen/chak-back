# Инструкции по запуску проекта

## Предварительные требования
1. Установите Python 3.7+
2. Установите MongoDB
3. Убедитесь, что MongoDB запущен на localhost:27017

## Установка зависимостей
`ash
pip install -r requirements.txt
`

## Запуск MongoDB
Убедитесь, что MongoDB запущен:
`ash
# Windows
net start MongoDB

# Linux/Mac
sudo systemctl start mongod
`

## Инициализация базы данных
`ash
python init_db.py
`

## Запуск приложения
`ash
python app.py
`

Приложение будет доступно по адресу: http://localhost:5000

## Тестирование API
`ash
python test_api.py
`

## API Endpoints

### POST /register
Регистрация нового пользователя
- Возвращает: user_id, token

### GET /cards
Получение всех карточек с татарскими словами
- Возвращает: список карточек

### POST /answer
Отправка ответа на карточку
- Параметры: user_id, token, card_id, is_correct

### GET /rating/words
Рейтинг пользователей по количеству изученных слов

### GET /rating/streak
Рейтинг пользователей по максимальному стрику

### GET /stats/<user_id>
Статистика конкретного пользователя

## Структура базы данных

### Коллекция users
- user_id: UUID пользователя
- token: токен доступа
- total_questions: общее количество вопросов
- correct_answers: количество правильных ответов
- current_streak: текущий стрик
- max_streak: максимальный стрик
- created_at: дата создания
- last_login: последний вход

### Коллекция cards
- card_id: UUID карточки
- tatar_word: татарское слово
- russian_translation: русский перевод
- difficulty: уровень сложности (easy/medium/hard)

### Коллекция answers
- user_id: UUID пользователя
- card_id: UUID карточки
- is_correct: правильность ответа
- answered_at: время ответа
